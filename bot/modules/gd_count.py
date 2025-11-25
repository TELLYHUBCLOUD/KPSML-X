#!/usr/bin/env python3
from pyrogram.handlers import MessageHandler
from pyrogram.filters import command

from bot import bot
from bot.helper.mirror_utils.upload_utils.gdriveTools import GoogleDriveHelper
from bot.helper.telegram_helper.message_utils import deleteMessage, sendMessage
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.ext_utils.bot_utils import is_gdrive_link, sync_to_async, new_task, get_readable_file_size
from bot.helper.themes import BotTheme


@new_task
async def countNode(_, message):
    """
    Counts the files and folders in a Google Drive link.
    """
    user_tag = f"@{message.from_user.username}" if message.from_user.username else message.from_user.mention

    args = message.text.split()
    link = args[1] if len(args) > 1 else ''
    if not link and (reply_to := message.reply_to_message):
        link = reply_to.text.split(maxsplit=1)[0].strip()

    if not is_gdrive_link(link):
        await sendMessage(message, 'Please provide a GDrive link.')
        return

    status_msg = await sendMessage(message, f'Counting files in <code>{link}</code>...')

    gd = GoogleDriveHelper()
    name, mime_type, size, files, folders = await sync_to_async(gd.count, link)

    await deleteMessage(status_msg)

    if not mime_type:
        await sendMessage(message, name)
        return

    msg = (
        f'<b>Name:</b> {name}\n'
        f'<b>Size:</b> {get_readable_file_size(size)}\n'
        f'<b>Type:</b> {mime_type}\n'
    )
    if mime_type == 'Folder':
        msg += f'<b>Folders:</b> {folders}\n'
        msg += f'<b>Files:</b> {files}\n'

    msg += f'<b>cc:</b> {user_tag}'

    await sendMessage(message, msg, photo='IMAGES')


bot.add_handler(MessageHandler(countNode, filters=command(BotCommands.CountCommand) & CustomFilters.authorized & ~CustomFilters.blacklisted))
