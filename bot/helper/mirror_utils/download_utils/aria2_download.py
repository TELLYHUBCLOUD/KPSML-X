#!/usr/bin/env python3
from aiofiles.os import remove as aioremove, path as aiopath

from bot import aria2, download_dict_lock, download_dict, LOGGER, config_dict, aria2_options, aria2c_global, non_queued_dl, queue_dict_lock
from bot.helper.ext_utils.bot_utils import bt_selection_buttons, sync_to_async
from bot.helper.mirror_utils.status_utils.aria2_status import Aria2Status
from bot.helper.telegram_helper.message_utils import sendStatusMessage, sendMessage
from bot.helper.ext_utils.task_manager import is_queued


async def add_aria2c_download(link, path, listener, filename, header, ratio, seed_time):
    """
    Adds a download to aria2c.
    """
    a2c_opt = {**aria2_options}
    [a2c_opt.pop(k, None) for k in aria2c_global if k in aria2_options]
    a2c_opt['dir'] = path

    if filename:
        a2c_opt['out'] = filename
    if header:
        a2c_opt['header'] = header
    if ratio:
        a2c_opt['seed-ratio'] = ratio
    if seed_time:
        a2c_opt['seed-time'] = seed_time
    if TORRENT_TIMEOUT := config_dict['TORRENT_TIMEOUT']:
        a2c_opt['bt-stop-timeout'] = str(TORRENT_TIMEOUT)

    added_to_queue, event = await is_queued(listener.uid)
    if added_to_queue:
        a2c_opt['pause-metadata' if link.startswith('magnet:') else 'pause'] = 'true'

    try:
        download = (await sync_to_async(aria2.add, link, a2c_opt))[0]
    except Exception as e:
        LOGGER.error(f"Aria2c download error: {e}")
        await sendMessage(listener.message, str(e))
        return

    if await aiopath.exists(link):
        await aioremove(link)

    if download.error_message:
        error = str(download.error_message).replace('<', ' ').replace('>', ' ')
        LOGGER.error(f"Aria2c download error: {error}")
        await sendMessage(listener.message, error)
        return

    gid = download.gid
    name = download.name

    async with download_dict_lock:
        download_dict[listener.uid] = Aria2Status(gid, listener, queued=added_to_queue)

    if added_to_queue:
        LOGGER.info(f"Added to queue/download: {name} - GID: {gid}")
        if not listener.select or not download.is_torrent:
            await sendStatusMessage(listener.message)
    else:
        async with queue_dict_lock:
            non_queued_dl.add(listener.uid)
        LOGGER.info(f"Aria2 download started: {name} - GID: {gid}")

    await listener.onDownloadStart()

    if not added_to_queue and (not listener.select or not config_dict['BASE_URL']):
        await sendStatusMessage(listener.message)
    elif listener.select and download.is_torrent and not download.is_metadata:
        if not added_to_queue:
            await sync_to_async(aria2.client.force_pause, gid)
        SBUTTONS = bt_selection_buttons(gid)
        msg = "✅ Your download is paused. Choose files and press 'Done Selecting' to start."
        await sendMessage(listener.message, msg, SBUTTONS)

    if added_to_queue:
        await event.wait()

        async with download_dict_lock:
            if listener.uid not in download_dict:
                return
            download = download_dict[listener.uid]
            download.queued = False
            new_gid = download.gid()

        await sync_to_async(aria2.client.unpause, new_gid)
        LOGGER.info(f'Started queued download from Aria2c: {name} - GID: {gid}')

        async with queue_dict_lock:
            non_queued_dl.add(listener.uid)
