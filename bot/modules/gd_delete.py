#!/usr/bin/env python3
from pyrogram.handlers import MessageHandler
from pyrogram.filters import command

from bot import bot, LOGGER
from bot.helper.telegram_helper.message_utils import auto_delete_message, sendMessage
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.mirror_utils.upload_utils.gdriveTools import GoogleDriveHelper
from bot.helper.ext_utils.bot_utils import is_gdrive_link, sync_to_async, new_task


@new_task
async def delete_file(_, message):
    """
    Deletes a file or folder from Google Drive.
    """
    args = message.text.split()

    if len(args) > 1:
        link = args[1]
    elif reply_to := message.reply_to_message:
        link = reply_to.text.split(maxsplit=1)[0].strip()
    else:
        link = ''

    if is_gdrive_link(link):
        LOGGER.info(f"Deleting GDrive link: {link}")
        drive = GoogleDriveHelper()
        result_msg = await sync_to_async(drive.deletefile, link)
    else:
        result_msg = 'Please provide a GDrive link to delete.'

    reply_message = await sendMessage(message, result_msg)
    await auto_delete_message(message, reply_message)


bot.add_handler(MessageHandler(delete_file, filters=command(BotCommands.DeleteCommand) & CustomFilters.authorized & ~CustomFilters.blacklisted))
