#!/usr/bin/env python3
from time import time
from asyncio import Event

from bot import bot_cache, config_dict, queued_dl, queued_up, non_queued_up, non_queued_dl, queue_dict_lock, LOGGER, user_data, download_dict
from bot.helper.mirror_utils.upload_utils.gdriveTools import GoogleDriveHelper
from bot.helper.ext_utils.fs_utils import get_base_name, check_storage_threshold
from bot.helper.ext_utils.bot_utils import get_user_tasks, getdailytasks, sync_to_async, get_telegraph_list, get_readable_file_size, checking_access, get_readable_time
from bot.helper.telegram_helper.message_utils import forcesub, check_botpm
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.themes import BotTheme


async def stop_duplicate_check(name, listener):
    """
    Checks if a file/folder with the same name already exists in the Drive.
    """
    if (
        not config_dict['STOP_DUPLICATE']
        or listener.isLeech
        or listener.upPath != 'gd'
        or listener.select
    ):
        return False, None

    LOGGER.info(f'🔎 Checking for duplicates in Drive: {name}')
    if listener.compress:
        name = f"{name}.zip"
    elif listener.extract:
        try:
            name = get_base_name(name)
        except Exception:
            name = None

    if name is not None:
        telegraph_content, contents_no = await sync_to_async(GoogleDriveHelper().drive_list, name, stopDup=True)
        if telegraph_content:
            msg = BotTheme('STOP_DUPLICATE', content=contents_no)
            button = await get_telegraph_list(telegraph_content)
            return msg, button
    return False, None


async def timeval_check(user_id):
    """
    Checks if the user is within the allowed time interval between tasks.
    """
    bot_cache.setdefault('time_interval', {})
    user_time = bot_cache['time_interval'].get(user_id)
    if user_time and (time() - user_time) < (UTI := config_dict['USER_TIME_INTERVAL']):
        return UTI - (time() - user_time)
    bot_cache['time_interval'][user_id] = time()
    return None


async def is_queued(uid):
    """
    Checks if a task should be added to the queue.
    """
    all_limit = config_dict['QUEUE_ALL']
    dl_limit = config_dict['QUEUE_DOWNLOAD']

    if not all_limit and not dl_limit:
        return False, None

    async with queue_dict_lock:
        dl_count = len(non_queued_dl)
        up_count = len(non_queued_up)

        if (all_limit and dl_count + up_count >= all_limit and (not dl_limit or dl_count >= dl_limit)) or \
           (dl_limit and dl_count >= dl_limit):
            event = Event()
            queued_dl[uid] = event
            return True, event

    return False, None


def start_dl_from_queued(uid):
    """
    Starts a download from the queue.
    """
    queued_dl[uid].set()
    del queued_dl[uid]


def start_up_from_queued(uid):
    """
    Starts an upload from the queue.
    """
    queued_up[uid].set()
    del queued_up[uid]


async def start_from_queued():
    """
    Starts tasks from the queue based on defined limits.
    """
    if all_limit := config_dict['QUEUE_ALL']:
        dl_limit = config_dict['QUEUE_DOWNLOAD']
        up_limit = config_dict['QUEUE_UPLOAD']
        async with queue_dict_lock:
            dl = len(non_queued_dl)
            up = len(non_queued_up)

            if (total := dl + up) < all_limit:
                tasks_to_start = all_limit - total
                if queued_up and (not up_limit or up < up_limit):
                    for i, uid in enumerate(list(queued_up.keys()), 1):
                        start_up_from_queued(uid)
                        tasks_to_start -= 1
                        if tasks_to_start == 0 or (up_limit and i >= up_limit - up):
                            break

                if queued_dl and (not dl_limit or dl < dl_limit) and tasks_to_start > 0:
                    for i, uid in enumerate(list(queued_dl.keys()), 1):
                        start_dl_from_queued(uid)
                        if (dl_limit and i >= dl_limit - dl) or i == tasks_to_start:
                            break
        return

    if up_limit := config_dict['QUEUE_UPLOAD']:
        async with queue_dict_lock:
            if queued_up and len(non_queued_up) < up_limit:
                for i, uid in enumerate(list(queued_up.keys()), 1):
                    start_up_from_queued(uid)
                    if i == up_limit - len(non_queued_up):
                        break
    else:
        async with queue_dict_lock:
            for uid in list(queued_up.keys()):
                start_up_from_queued(uid)

    if dl_limit := config_dict['QUEUE_DOWNLOAD']:
        async with queue_dict_lock:
            if queued_dl and len(non_queued_dl) < dl_limit:
                for i, uid in enumerate(list(queued_dl.keys()), 1):
                    start_dl_from_queued(uid)
                    if i == dl_limit - len(non_queued_dl):
                        break
    else:
        async with queue_dict_lock:
            for uid in list(queued_dl.keys()):
                start_dl_from_queued(uid)


async def limit_checker(size, listener, isTorrent=False, isMega=False, isDriveLink=False, isYtdlp=False, isPlayList=None):
    """
    Checks if a task exceeds defined limits.
    """
    user_id = listener.message.from_user.id
    if await CustomFilters.sudo('', listener.message):
        return

    limit_exceeded = []

    def check_limit(limit_value, limit_name):
        if limit_value and size > limit_value * 1024**3:
            limit_exceeded.append(f'{limit_name} limit is {get_readable_file_size(limit_value * 1024**3)}.')

    if listener.isClone:
        check_limit(config_dict['CLONE_LIMIT'], 'Clone')
    elif isMega:
        check_limit(config_dict['MEGA_LIMIT'], 'Mega')
    elif isDriveLink:
        check_limit(config_dict['GDRIVE_LIMIT'], 'GDrive')
    elif isYtdlp:
        check_limit(config_dict['YTDLP_LIMIT'], 'Ytdlp')
        if isPlayList and (playlist_limit := config_dict['PLAYLIST_LIMIT']) and isPlayList > playlist_limit:
            limit_exceeded.append(f'Playlist limit is {playlist_limit}.')
    elif isTorrent:
        check_limit(config_dict['TORRENT_LIMIT'], 'Torrent')
    else:
        check_limit(config_dict['DIRECT_LIMIT'], 'Direct')

    if not limit_exceeded:
        if listener.isLeech:
            check_limit(config_dict['LEECH_LIMIT'], 'Leech')

        if (threshold := config_dict['STORAGE_THRESHOLD']) and not listener.isClone:
            arch = listener.compress or listener.extract
            limit = threshold * 1024**3
            if not await sync_to_async(check_storage_threshold, size, limit, arch):
                limit_exceeded.append(f'You must leave {get_readable_file_size(limit)} free storage.')

        if (daily_task_limit := config_dict['DAILY_TASK_LIMIT']) and daily_task_limit <= await getdailytasks(user_id):
            limit_exceeded.append(f"Daily task limit reached: {daily_task_limit}.")
        else:
            await getdailytasks(user_id, increase_task=True)

        if not listener.isLeech and (daily_mirror_limit := config_dict['DAILY_MIRROR_LIMIT']):
            limit = daily_mirror_limit * 1024**3
            if size + await getdailytasks(user_id, check_mirror=True) > limit:
                limit_exceeded.append(f'Daily mirror limit is {get_readable_file_size(limit)}.')
            else:
                await getdailytasks(user_id, upmirror=size)

        if listener.isLeech and (daily_leech_limit := config_dict['DAILY_LEECH_LIMIT']):
            limit = daily_leech_limit * 1024**3
            if size + await getdailytasks(user_id, check_leech=True) > limit:
                limit_exceeded.append(f'Daily leech limit is {get_readable_file_size(limit)}.')
            else:
                await getdailytasks(user_id, upleech=size)

    if limit_exceeded:
        return f"{' '.join(limit_exceeded)}\nYour file size is {get_readable_file_size(size)}."


async def task_utils(message):
    """
    Manages task execution by checking various user and bot limits.
    """
    msg = []
    button = None

    if await CustomFilters.sudo('', message):
        return msg, button

    user_id = message.from_user.id

    token_msg, button = await checking_access(user_id, button)
    if token_msg:
        msg.append(token_msg)

    if message.chat.type != message.chat.type.BOT:
        if fsub_ids := config_dict['FSUB_IDS']:
            fsub_msg, button = await forcesub(message, fsub_ids, button)
            if fsub_msg:
                msg.append(fsub_msg)

        user_dict = user_data.get(user_id, {})
        if config_dict['BOT_PM'] or user_dict.get('bot_pm') or config_dict['SAFE_MODE']:
            bot_pm_msg, button = await check_botpm(message, button)
            if bot_pm_msg:
                msg.append(bot_pm_msg)

    if (uti := config_dict['USER_TIME_INTERVAL']) and (remaining_time := await timeval_check(user_id)):
        msg.append(f"⏳ Please wait {get_readable_time(remaining_time)} before starting a new task.")

    if (bmax_tasks := config_dict['BOT_MAX_TASKS']) and len(download_dict) >= bmax_tasks:
        msg.append(f"🚦 Bot is busy. Max tasks limit ({bmax_tasks}) reached. Please wait.")

    if (maxtask := config_dict['USER_MAX_TASKS']) and await get_user_tasks(user_id, maxtask):
        msg.append(f"✋ Your task limit of {maxtask} has been reached.")

    return msg, button
