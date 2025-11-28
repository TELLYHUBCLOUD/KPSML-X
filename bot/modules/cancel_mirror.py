#!/usr/bin/env python3
from asyncio import sleep
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from pyrogram.filters import command, regex

from bot import download_dict, bot, bot_name, download_dict_lock, OWNER_ID, user_data
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.message_utils import sendMessage, deleteMessage, auto_delete_message
from bot.helper.ext_utils.bot_utils import getDownloadByGid, getAllDownload, MirrorStatus, new_task
from bot.helper.telegram_helper import button_build


async def cancel_mirror(_, message):
    """
    Cancels a single download task.
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
        await sendMessage(message, f"Reply to an active task or use <code>/{BotCommands.CancelMirror}_GID</code>.")
        return

    if (
        OWNER_ID != user_id and
        dl.message.from_user.id != user_id and
        (not user_data.get(user_id) or not user_data[user_id].get('is_sudo'))
    ):
        await sendMessage(message, "This task is not for you.")
        return

    await dl.download().cancel_download()


async def cancel_all(status):
    """
    Cancels all tasks based on their status.
    """
    matches = await getAllDownload(status)
    if not matches:
        return False

    for dl in matches:
        await dl.download().cancel_download()
        await sleep(1)

    return True


async def cancell_all_buttons(_, message):
    """
    Displays buttons to cancel all tasks by status.
    """
    async with download_dict_lock:
        count = len(download_dict)
    if count == 0:
        await sendMessage(message, "No active tasks.")
        return

    buttons = button_build.ButtonMaker()
    buttons.ibutton("Downloading", f"canall {MirrorStatus.STATUS_DOWNLOADING}")
    buttons.ibutton("Uploading", f"canall {MirrorStatus.STATUS_UPLOADING}")
    buttons.ibutton("Seeding", f"canall {MirrorStatus.STATUS_SEEDING}")
    buttons.ibutton("Cloning", f"canall {MirrorStatus.STATUS_CLONING}")
    buttons.ibutton("Extracting", f"canall {MirrorStatus.STATUS_EXTRACTING}")
    buttons.ibutton("Archiving", f"canall {MirrorStatus.STATUS_ARCHIVING}")
    buttons.ibutton("QueuedDL", f"canall {MirrorStatus.STATUS_QUEUEDL}")
    buttons.ibutton("QueuedUp", f"canall {MirrorStatus.STATUS_QUEUEUP}")
    buttons.ibutton("Paused", f"canall {MirrorStatus.STATUS_PAUSED}")
    buttons.ibutton("All", "canall all")
    buttons.ibutton("Close", "canall close")

    can_msg = await sendMessage(message, 'Choose task types to cancel.', buttons.build_menu(2))
    await auto_delete_message(message, can_msg)


@new_task
async def cancel_all_update(_, query):
    """
    Handles the callback query for cancelling all tasks.
    """
    data = query.data.split()
    message = query.message
    reply_to = message.reply_to_message
    await query.answer()

    if data[1] == 'close':
        await deleteMessage(reply_to)
        await deleteMessage(message)
    elif not await cancel_all(data[1]):
        await sendMessage(reply_to, f"No tasks found for status: {data[1]}")


bot.add_handler(MessageHandler(cancel_mirror, filters=regex(f"^/{BotCommands.CancelMirror}(_\w+)?(?!all)") & CustomFilters.authorized & ~CustomFilters.blacklisted))
bot.add_handler(MessageHandler(cancell_all_buttons, filters=command(BotCommands.CancelAllCommand) & CustomFilters.sudo))
bot.add_handler(CallbackQueryHandler(cancel_all_update, filters=regex(r"^canall")))
