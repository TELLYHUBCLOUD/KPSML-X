#!/usr/bin/env python3
from asyncio import sleep
from time import time
from aiofiles.os import remove as aioremove, path as aiopath

from bot import aria2, download_dict_lock, download_dict, LOGGER, config_dict
from bot.helper.ext_utils.task_manager import limit_checker
from bot.helper.mirror_utils.upload_utils.gdriveTools import GoogleDriveHelper
from bot.helper.mirror_utils.status_utils.aria2_status import Aria2Status
from bot.helper.ext_utils.fs_utils import get_base_name, clean_unwanted
from bot.helper.ext_utils.bot_utils import getDownloadByGid, new_thread, bt_selection_buttons, sync_to_async, get_telegraph_list
from bot.helper.telegram_helper.message_utils import sendMessage, deleteMessage, update_all_messages
from bot.helper.themes import BotTheme


@new_thread
async def __onDownloadStarted(api, gid):
    """
    Handles the onDownloadStarted event for aria2c.
    """
    download = await sync_to_async(api.get_download, gid)
    if download.options.follow_torrent == 'false':
        return

    if download.is_metadata:
        LOGGER.info(f'onDownloadStarted: {gid} METADATA')
        await sleep(1)
        if dl := await getDownloadByGid(gid):
            listener = dl.listener()
            if listener.select:
                metamsg = "⏳ Downloading metadata, please wait for file selection..."
                meta = await sendMessage(listener.message, metamsg)
                while True:
                    await sleep(0.5)
                    if download.is_removed or download.followed_by_ids:
                        await deleteMessage(meta)
                        break
                    download = download.live
        return
    else:
        LOGGER.info(f'onDownloadStarted: {download.name} - Gid: {gid}')

    dl = None
    if any([config_dict['DIRECT_LIMIT'],
            config_dict['TORRENT_LIMIT'],
            config_dict['LEECH_LIMIT'],
            config_dict['STORAGE_THRESHOLD'],
            config_dict['DAILY_TASK_LIMIT'],
            config_dict['DAILY_MIRROR_LIMIT'],
            config_dict['DAILY_LEECH_LIMIT']]):
        await sleep(1)
        dl = dl or await getDownloadByGid(gid)
        if dl and hasattr(dl, 'listener'):
            listener = dl.listener()
            download = await sync_to_async(api.get_download, gid)
            if not download.is_torrent:
                await sleep(3)
                download = download.live
            size = download.total_length
            LOGGER.info(f"Checking limit for {download.name}: {size}")
            if limit_exceeded := await limit_checker(size, listener):
                await listener.onDownloadError(limit_exceeded)
                await sync_to_async(api.remove, [download], force=True, files=True)

    if config_dict['STOP_DUPLICATE']:
        await sleep(1)
        dl = dl or await getDownloadByGid(gid)
        if dl and hasattr(dl, 'listener'):
            listener = dl.listener()
            if not listener.isLeech and not listener.select and listener.upPath == 'gd':
                download = await sync_to_async(api.get_download, gid)
                if not download.is_torrent:
                    await sleep(3)
                    download = download.live

                name = download.name
                if listener.compress:
                    name = f"{name}.zip"
                elif listener.extract:
                    try:
                        name = get_base_name(name)
                    except Exception:
                        name = None

                if name:
                    LOGGER.info(f'Checking for duplicates in Drive: {name}')
                    telegraph_content, contents_no = await sync_to_async(GoogleDriveHelper().drive_list, name, True)
                    if telegraph_content:
                        msg = BotTheme('STOP_DUPLICATE', content=contents_no)
                        button = await get_telegraph_list(telegraph_content)
                        await listener.onDownloadError(msg, button)
                        await sync_to_async(api.remove, [download], force=True, files=True)


@new_thread
async def __onDownloadComplete(api, gid):
    """
    Handles the onDownloadComplete event for aria2c.
    """
    try:
        download = await sync_to_async(api.get_download, gid)
    except Exception:
        return

    if download.options.follow_torrent == 'false' or download.is_metadata:
        return

    if download.followed_by_ids:
        new_gid = download.followed_by_ids[0]
        LOGGER.info(f'GID changed from {gid} to {new_gid}')
        if dl := await getDownloadByGid(new_gid):
            listener = dl.listener()
            if config_dict['BASE_URL'] and listener.select:
                if not dl.queued:
                    await sync_to_async(api.client.force_pause, new_gid)
                SBUTTONS = bt_selection_buttons(new_gid)
                msg = "✅ Your download is paused. Choose files and press 'Done Selecting' to start."
                await sendMessage(listener.message, msg, SBUTTONS)
    elif download.is_torrent:
        if dl := await getDownloadByGid(gid):
            if hasattr(dl, 'listener') and dl.seeding:
                LOGGER.info(f"Seeding completed: {download.name}")
                listener = dl.listener()
                await listener.onUploadError(f"Seeding stopped at Ratio: {dl.ratio()} and Time: {dl.seeding_time()}")
                await sync_to_async(api.remove, [download], force=True, files=True)
    else:
        LOGGER.info(f"Download completed: {download.name} - GID: {gid}")
        if dl := await getDownloadByGid(gid):
            listener = dl.listener()
            await listener.onDownloadComplete()
            await sync_to_async(api.remove, [download], force=True, files=True)


@new_thread
async def __onBtDownloadComplete(api, gid):
    """
    Handles the onBtDownloadComplete event for aria2c (torrents).
    """
    seed_start_time = time()
    await sleep(1)
    download = await sync_to_async(api.get_download, gid)

    if download.options.follow_torrent == 'false':
        return

    LOGGER.info(f"BT download completed: {download.name} - GID: {gid}")
    if dl := await getDownloadByGid(gid):
        listener = dl.listener()
        if listener.select:
            for file_obj in download.files:
                if not file_obj.selected and await aiopath.exists(file_obj.path):
                    try:
                        await aioremove(file_obj.path)
                    except Exception as e:
                        LOGGER.warning(f"Failed to remove unselected file: {file_obj.path} - {e}")
            await clean_unwanted(download.dir)

        if listener.seed:
            try:
                await sync_to_async(api.set_options, {'max-upload-limit': '0'}, [download])
            except Exception as e:
                LOGGER.error(f"{e} - Failed to disable upload limit for seeding. GID: {gid}")
        else:
            try:
                await sync_to_async(api.client.force_pause, gid)
            except Exception as e:
                LOGGER.error(f"{e} - Failed to pause download. GID: {gid}")

        await listener.onDownloadComplete()
        download = download.live

        if listener.seed:
            if download.is_complete:
                if dl := await getDownloadByGid(gid):
                    LOGGER.info(f"Seeding finished: {download.name}")
                    await listener.onUploadError(f"Seeding stopped at Ratio: {dl.ratio()} and Time: {dl.seeding_time()}")
                    await sync_to_async(api.remove, [download], force=True, files=True)
            else:
                async with download_dict_lock:
                    if listener.uid not in download_dict:
                        await sync_to_async(api.remove, [download], force=True, files=True)
                        return
                    download_dict[listener.uid] = Aria2Status(gid, listener, True)
                    download_dict[listener.uid].start_time = seed_start_time
                LOGGER.info(f"Seeding started: {download.name} - GID: {gid}")
                await update_all_messages()
        else:
            await sync_to_async(api.remove, [download], force=True, files=True)


@new_thread
async def __onDownloadStopped(api, gid):
    """
    Handles the onDownloadStopped event for aria2c.
    """
    await sleep(6)
    if dl := await getDownloadByGid(gid):
        listener = dl.listener()
        await listener.onDownloadError('❌ Download stopped: Dead torrent!')


@new_thread
async def __onDownloadError(api, gid):
    """
    Handles the onDownloadError event for aria2c.
    """
    LOGGER.info(f"Download error: {gid}")
    error = "Unknown error"
    try:
        download = await sync_to_async(api.get_download, gid)
        if download.options.follow_torrent != 'false':
            error = download.error_message
            LOGGER.error(f"Aria2 download error: {error}")
    except Exception as e:
        LOGGER.error(f"Exception while getting download error message: {e}")

    if dl := await getDownloadByGid(gid):
        listener = dl.listener()
        await listener.onDownloadError(error)


def start_aria2_listener():
    """
    Starts the aria2 event listener.
    """
    aria2.listen_to_notifications(threaded=False,
                                  on_download_start=__onDownloadStarted,
                                  on_download_error=__onDownloadError,
                                  on_download_stop=__onDownloadStopped,
                                  on_download_complete=__onDownloadComplete,
                                  on_bt_download_complete=__onBtDownloadComplete,
                                  timeout=60)
