#!/usr/bin/env python3
from pyrogram.filters import command, regex
from pyrogram.handlers import CallbackQueryHandler, MessageHandler
from time import time

from bot import bot, bot_cache, categories_dict, download_dict, download_dict_lock
from bot.helper.ext_utils.bot_utils import (
    MirrorStatus, arg_parser, fetch_user_tds, fetch_user_dumps, getDownloadByGid,
    is_gdrive_link, new_task, sync_to_async, get_readable_time
)
from bot.helper.ext_utils.help_messages import CATEGORY_HELP_MESSAGE
from bot.helper.mirror_utils.upload_utils.gdriveTools import GoogleDriveHelper
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.button_build import ButtonMaker
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.message_utils import editMessage, sendMessage, open_category_btns


async def change_category(_, message):
    """
    Changes the category of an active download.
    """
    if not message.from_user:
        return

    user_id = message.from_user.id
    args = arg_parser(message.text.split()[1:], {'-id': '', '-index': ''})

    drive_id = args['-id']
    index_link = args['-index']

    if drive_id and is_gdrive_link(drive_id):
        drive_id = GoogleDriveHelper.getIdFromUrl(drive_id)

    dl = None
    if gid := args['link']:
        dl = await getDownloadByGid(gid)
        if not dl:
            await sendMessage(message, f"GID <code>{gid}</code> not found.")
            return

    if reply_to := message.reply_to_message:
        async with download_dict_lock:
            dl = download_dict.get(reply_to.id)
        if not dl:
            await sendMessage(message, "This is not an active task.")
            return

    if not dl:
        await sendMessage(message, CATEGORY_HELP_MESSAGE)
        return

    if not await CustomFilters.sudo(None, message) and dl.message.from_user.id != user_id:
        await sendMessage(message, "This task is not for you.")
        return

    if dl.status() not in [MirrorStatus.STATUS_DOWNLOADING, MirrorStatus.STATUS_PAUSED, MirrorStatus.STATUS_QUEUEDL]:
        await sendMessage(message, f'Task must be in downloading, paused, or queued state.')
        return

    listener = dl.listener()
    if not listener or listener.isLeech:
        await sendMessage(message, "Cannot change the category for this task.")
        return

    if not index_link and not drive_id and categories_dict:
        drive_id, index_link, is_cancelled = await open_category_btns(message)
        if is_cancelled:
            return

    if not index_link and not drive_id:
        await sendMessage(message, "Task timed out.")
        return

    msg = '<b>✅ Task has been updated successfully!</b>'

    if drive_id:
        folder_name = await sync_to_async(GoogleDriveHelper().getFolderData, drive_id)
        if not folder_name:
            await sendMessage(message, "Google Drive ID validation failed.")
            return
        msg += f'\n\n<b>📁 Folder:</b> {folder_name}'
        listener.drive_id = drive_id

    if index_link:
        listener.index_link = index_link
        msg += f'\n\n<b>🔗 Index Link:</b> <code>{index_link}</code>'

    await sendMessage(message, msg)


@new_task
async def confirm_category(_, query):
    """
    Handles the callback query for category selection.
    """
    user_id = query.from_user.id
    data = query.data.split(maxsplit=3)
    msg_id = int(data[2])

    if msg_id not in bot_cache:
        await editMessage(query.message, '<b>Old task.</b>')
        return

    if user_id != int(data[1]) and not await CustomFilters.sudo(None, query):
        await query.answer("This task is not for you!", show_alert=True)
        return

    if data[3] == "sdone":
        bot_cache[msg_id][2] = True
        return

    if data[3] == "scancel":
        bot_cache[msg_id][3] = True
        return

    await query.answer()

    user_tds = await fetch_user_tds(user_id)
    merged_dict = {**categories_dict, **user_tds}
    cat_name = data[3].replace('_', ' ')

    bot_cache[msg_id][0] = merged_dict[cat_name].get('drive_id')
    bot_cache[msg_id][1] = merged_dict[cat_name].get('index_link')

    buttons = ButtonMaker()
    for name in merged_dict:
        buttons.ibutton(f'{"✅️" if cat_name == name else ""} {name}', f"scat {user_id} {msg_id} {name.replace(' ', '_')}")

    buttons.ibutton('❌ Cancel', f'scat {user_id} {msg_id} scancel', 'footer')
    buttons.ibutton(f'Done ({get_readable_time(60 - (time() - bot_cache[msg_id][4]))})', f'scat {user_id} {msg_id} sdone', 'footer')

    await editMessage(query.message, f"<b>Select an upload category</b>\n\n<b>Current:</b> <code>{cat_name}</code>\n\n<b>Timeout:</b> 60s", buttons.build_menu(2))


# Dump functions would be refactored similarly

bot.add_handler(MessageHandler(change_category, filters=command(BotCommands.CategorySelect) & CustomFilters.authorized))
bot.add_handler(CallbackQueryHandler(confirm_category, filters=regex("^scat")))
# bot.add_handler(CallbackQueryHandler(confirm_dump, filters=regex("^dcat")))
