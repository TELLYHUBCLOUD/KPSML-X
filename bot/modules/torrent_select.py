#!/usr/bin/env python3
from contextlib import suppress
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from pyrogram.filters import regex
from aiofiles.os import remove as aioremove, path as aiopath

from bot import bot, bot_name, aria2, download_dict, download_dict_lock, OWNER_ID, user_data, LOGGER
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.message_utils import sendMessage, sendStatusMessage, deleteMessage
from bot.helper.ext_utils.bot_utils import getDownloadByGid, MirrorStatus, bt_selection_buttons, sync_to_async


async def select(_, message):
    """
    Selects files from a torrent to download.
    """
    user_id = message.from_user.id
    msg_parts = message.text.split('_', maxsplit=1)

    gid = None
    dl = None

    if len(msg_parts) > 1:
        cmd_data = msg_parts[1].split('@', maxsplit=1)
        if len(cmd_data) > 1 and cmd_data[1].strip() != bot_name:
            return
        gid = cmd_data[0]
        dl = await getDownloadByGid(gid)
        if not dl:
            await sendMessage(message, f"GID <code>{gid}</code> not found.")
            return
    elif reply_to_id := message.reply_to_message_id:
        async with download_dict_lock:
            dl = download_dict.get(reply_to_id)
        if not dl:
            await sendMessage(message, "This is not an active task.")
            return
    else:
        await sendMessage(message, "Reply to an active task or use <code>/btsel_GID</code>.")
        return

    if (
        OWNER_ID != user_id and
        dl.message.from_user.id != user_id and
        (not user_data.get(user_id) or not user_data[user_id].get('is_sudo'))
    ):
        await sendMessage(message, "This task is not for you.")
        return

    if dl.status() not in [MirrorStatus.STATUS_DOWNLOADING, MirrorStatus.STATUS_PAUSED, MirrorStatus.STATUS_QUEUEDL]:
        await sendMessage(message, 'Task must be in downloading, paused, or queued state.')
        return

    if dl.name().startswith('[METADATA]'):
        await sendMessage(message, 'Try again after the metadata has been downloaded.')
        return

    try:
        listener = dl.listener()
        if listener.isQbit:
            id_ = dl.hash()
            client = dl.client()
            if not dl.queued:
                await sync_to_async(client.torrents_pause, torrent_hashes=id_)
        else:
            id_ = dl.gid()
            if not dl.queued:
                await sync_to_async(aria2.client.force_pause, id_)
        listener.select = True
    except Exception as e:
        await sendMessage(message, f"This is not a bittorrent task: {e}")
        return

    SBUTTONS = bt_selection_buttons(id_)
    msg = "✅ Your download is paused. Choose files and press 'Done Selecting' to resume."
    await sendMessage(message, msg, SBUTTONS)


async def get_confirm(_, query):
    """
    Handles the callback query for torrent file selection.
    """
    user_id = query.from_user.id
    data = query.data.split()
    message = query.message

    dl = await getDownloadByGid(data[2])
    if not dl:
        await query.answer("This task has been cancelled!", show_alert=True)
        await deleteMessage(message)
        return

    listener = getattr(dl, 'listener', None)
    if not listener:
        await query.answer("Task is no longer in a downloadable state.", show_alert=True)
        return

    if user_id != listener.message.from_user.id and not await CustomFilters.sudo(None, query):
        await query.answer("This task is not for you!", show_alert=True)
        return

    if data[1] == "pin":
        await query.answer(data[3], show_alert=True)
    elif data[1] == "done":
        await query.answer()
        id_ = data[3]
        if len(id_) > 20: # qBittorrent
            client = dl.client()
            tor_info = (await sync_to_async(client.torrents_info, torrent_hash=id_))[0]
            path = tor_info.content_path.rsplit('/', 1)[0]
            res = await sync_to_async(client.torrents_files, torrent_hash=id_)
            for f in res:
                if f.priority == 0:
                    f_path = f"{path}/{f.name}"
                    if await aiopath.exists(f_path):
                        with suppress(Exception): await aioremove(f_path)
                    if await aiopath.exists(f"{f_path}.!qB"):
                        with suppress(Exception): await aioremove(f"{f_path}.!qB")
            if not dl.queued:
                await sync_to_async(client.torrents_resume, torrent_hashes=id_)
        else: # aria2
            res = await sync_to_async(aria2.client.get_files, id_)
            for f in res:
                if f['selected'] == 'false' and await aiopath.exists(f['path']):
                    with suppress(Exception): await aioremove(f['path'])
            if not dl.queued:
                try:
                    await sync_to_async(aria2.client.unpause, id_)
                except Exception as e:
                    LOGGER.error(f"Aria2 resume error: {e}")

        await sendStatusMessage(message)
        await deleteMessage(message)

    elif data[1] == "rm":
        await query.answer()
        await dl.download().cancel_download()
        await deleteMessage(message)


bot.add_handler(MessageHandler(select, filters=regex(f"^/{BotCommands.BtSelectCommand}(_\w+)?") & CustomFilters.authorized & ~CustomFilters.blacklisted))
bot.add_handler(CallbackQueryHandler(get_confirm, filters=regex("^btsel")))
