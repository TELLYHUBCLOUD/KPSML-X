#!/usr/bin/env python3
from time import time
from aiofiles.os import remove as aioremove, path as aiopath

from bot import download_dict, download_dict_lock, get_client, LOGGER, config_dict, non_queued_dl, queue_dict_lock
from bot.helper.mirror_utils.status_utils.qbit_status import QbittorrentStatus
from bot.helper.telegram_helper.message_utils import sendMessage, deleteMessage, sendStatusMessage
from bot.helper.ext_utils.bot_utils import bt_selection_buttons, sync_to_async
from bot.helper.listeners.qbit_listener import onDownloadStart
from bot.helper.ext_utils.task_manager import is_queued


async def add_qb_torrent(link, path, listener, ratio, seed_time):
    """
    Adds a torrent to qBittorrent.
    """
    client = await sync_to_async(get_client)
    ADD_TIME = time()

    try:
        url = link
        tpath = None
        if await aiopath.exists(link):
            url = None
            tpath = link

        added_to_queue, event = await is_queued(listener.uid)

        op = await sync_to_async(client.torrents_add, url, tpath, path, is_paused=added_to_queue,
                                 tags=f'{listener.uid}', ratio_limit=ratio, seeding_time_limit=seed_time,
                                 headers={'user-agent': 'Wget/1.12'})

        if op.lower() != "ok.":
            await sendMessage(listener.message, "Torrent already added or invalid link/file.")
            return

        tor_info = await sync_to_async(client.torrents_info, tag=f'{listener.uid}')
        if not tor_info:
            while time() - ADD_TIME < 120:
                tor_info = await sync_to_async(client.torrents_info, tag=f'{listener.uid}')
                if tor_info:
                    break
            if not tor_info:
                await sendMessage(listener.message, "Failed to add torrent. Check if the link is valid or report if it's a torrent file.")
                return

        tor_info = tor_info[0]
        ext_hash = tor_info.hash

        async with download_dict_lock:
            download_dict[listener.uid] = QbittorrentStatus(listener, queued=added_to_queue)

        await onDownloadStart(f'{listener.uid}')

        if added_to_queue:
            LOGGER.info(f"Added to queue/download: {tor_info.name} - Hash: {ext_hash}")
        else:
            async with queue_dict_lock:
                non_queued_dl.add(listener.uid)
            LOGGER.info(f"qBittorrent download started: {tor_info.name} - Hash: {ext_hash}")

        await listener.onDownloadStart()

        if config_dict['BASE_URL'] and listener.select:
            if link.startswith('magnet:'):
                meta_msg = await sendMessage(listener.message, "⏳ Downloading metadata, please wait for file selection...")
                while True:
                    tor_info_list = await sync_to_async(client.torrents_info, tag=f'{listener.uid}')
                    if not tor_info_list:
                        await deleteMessage(meta_msg)
                        return
                    tor_info = tor_info_list[0]
                    if tor_info.state not in ["metaDL", "checkingResumeData", "pausedDL"]:
                        await deleteMessage(meta_msg)
                        break

            ext_hash = tor_info.hash
            if not added_to_queue:
                await sync_to_async(client.torrents_pause, torrent_hashes=ext_hash)

            SBUTTONS = bt_selection_buttons(ext_hash)
            msg = "✅ Your download is paused. Choose files and press 'Done Selecting' to start."
            await sendMessage(listener.message, msg, SBUTTONS)
        else:
            await sendStatusMessage(listener.message)

        if added_to_queue:
            await event.wait()
            async with download_dict_lock:
                if listener.uid not in download_dict:
                    return
                download_dict[listener.uid].queued = False

            await sync_to_async(client.torrents_resume, torrent_hashes=ext_hash)
            LOGGER.info(f'Started queued qBittorrent download: {tor_info.name} - Hash: {ext_hash}')

            async with queue_dict_lock:
                non_queued_dl.add(listener.uid)

    except Exception as e:
        await sendMessage(listener.message, str(e))
    finally:
        if await aiopath.exists(link):
            await aioremove(link)
