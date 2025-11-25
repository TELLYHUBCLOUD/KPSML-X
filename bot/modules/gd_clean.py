#!/usr/bin/env python3
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from pyrogram.filters import command, regex

from bot import bot, LOGGER, OWNER_ID, config_dict
from bot.helper.telegram_helper.message_utils import sendMessage, editMessage, auto_delete_message
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.button_build import ButtonMaker
from bot.helper.mirror_utils.upload_utils.gdriveTools import GoogleDriveHelper
from bot.helper.ext_utils.bot_utils import sync_to_async, new_task, is_gdrive_link, get_readable_file_size


@new_task
async def drive_clean(_, message):
    """
    Cleans a Google Drive folder by moving its contents to trash or deleting them permanently.
    """
    if len(message.command) > 1:
        link = message.command[1].strip()
    elif reply_to := message.reply_to_message:
        link = reply_to.text.split(maxsplit=1)[0].strip()
    else:
        link = f"https://drive.google.com/drive/folders/{config_dict.get('GDRIVE_ID')}"

    if not is_gdrive_link(link):
        await sendMessage(message, 'Please provide a valid GDrive link.')
        return

    status_msg = await sendMessage(message, '<i>Fetching folder data...</i>')

    gd = GoogleDriveHelper()
    name, mime_type, size, files, folders = await sync_to_async(gd.count, link)

    try:
        drive_id = GoogleDriveHelper.getIdFromUrl(link)
    except (KeyError, IndexError):
        await editMessage(status_msg, "Invalid G-Drive ID in the link.")
        return

    buttons = ButtonMaker()
    buttons.ibutton('♻️ Move to Bin', f'gdclean clear {drive_id} trash')
    buttons.ibutton('🗑️ Permanent Clean', f'gdclean clear {drive_id}')
    buttons.ibutton('❌ Stop', 'gdclean stop', 'footer')
    
    await editMessage(
        status_msg,
        f'<b>🧹 GDrive Clean/Trash</b>\n\n'
        f'<b>Name:</b> {name}\n'
        f'<b>Size:</b> {get_readable_file_size(size)}\n'
        f'<b>Files:</b> {files} | <b>Folders:</b> {folders}\n\n'
        '<b>Notes:</b>\n'
        '1. Files will be permanently deleted if "Permanent Clean" is chosen.\n'
        '2. The folder itself will not be deleted.\n'
        '3. Use a custom folder link to clean a specific folder.\n'
        '4. "Move to Bin" will move files to trash for easy restoration.\n\n'
        'Choose an action below:',
        buttons.build_menu(2)
    )


@new_task
async def drive_clean_callback(_, query):
    """
    Handles the callback query for the GDrive clean command.
    """
    message = query.message
    user_id = query.from_user.id
    data = query.data.split()

    if user_id != OWNER_ID:
        await query.answer("This is not for you!", show_alert=True)
        return

    if data[1] == "clear":
        await query.answer()
        await editMessage(message, '<i>Processing GDrive Clean/Trash...</i>')
        drive = GoogleDriveHelper()
        is_trash = len(data) == 4 and data[3] == 'trash'
        result_msg = await sync_to_async(drive.driveclean, data[2], trash=is_trash)
        await editMessage(message, result_msg)
    elif data[1] == "stop":
        await query.answer()
        await editMessage(message, '<b>GDrive Clean has been stopped.</b>')
        await auto_delete_message(message, message)
        

bot.add_handler(MessageHandler(drive_clean, filters=command(BotCommands.GDCleanCommand) & CustomFilters.owner))
bot.add_handler(CallbackQueryHandler(drive_clean_callback, filters=regex(r'^gdclean')))
