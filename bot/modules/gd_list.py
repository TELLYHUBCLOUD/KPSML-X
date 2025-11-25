#!/usr/bin/env python3
from random import choice
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from pyrogram.filters import command, regex

from bot import LOGGER, bot, config_dict
from bot.helper.mirror_utils.upload_utils.gdriveTools import GoogleDriveHelper
from bot.helper.telegram_helper.message_utils import sendMessage, editMessage, delete_links
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.button_build import ButtonMaker
from bot.helper.ext_utils.bot_utils import sync_to_async, new_task, get_telegraph_list, checking_access
from bot.helper.themes import BotTheme


async def list_buttons(user_id, is_recursive=True):
    """
    Creates buttons for GDrive list options.
    """
    buttons = ButtonMaker()
    buttons.ibutton("Folders", f"list_types {user_id} folders {is_recursive}")
    buttons.ibutton("Files", f"list_types {user_id} files {is_recursive}")
    buttons.ibutton("Both", f"list_types {user_id} both {is_recursive}")
    buttons.ibutton(f"{'✅ ' if is_recursive else ''}Recursive", f"list_types {user_id} rec {is_recursive}")
    buttons.ibutton("Cancel", f"list_types {user_id} cancel")
    return buttons.build_menu(2)


async def _list_drive(key, message, user_id, item_type, is_recursive):
    """
    Performs a GDrive search and sends the results.
    """
    LOGGER.info(f"GDrive List: {key}")
    gdrive = GoogleDriveHelper()
    telegraph_content, contents_no = await sync_to_async(gdrive.drive_list, key, isRecursive=is_recursive, itemType=item_type, userId=user_id)

    if telegraph_content:
        try:
            button = await get_telegraph_list(telegraph_content)
            msg = f"Found {contents_no} results for <code>{key}</code>."
            await editMessage(message, msg, button)
        except Exception as e:
            await editMessage(message, str(e))
    else:
        await editMessage(message, f"No results found for <code>{key}</code>.")


@new_task
async def select_type(_, query):
    """
    Handles the callback query for selecting list options.
    """
    user_id = query.from_user.id
    message = query.message
    key = message.reply_to_message.text.split(maxsplit=1)[1].strip()
    data = query.data.split()

    if user_id != int(data[1]):
        await query.answer("This is not for you!", show_alert=True)
        return

    action = data[2]
    is_recursive = eval(data[3]) if len(data) > 3 else True

    if action == 'rec':
        await query.answer()
        is_recursive = not is_recursive
        buttons = await list_buttons(user_id, is_recursive)
        await editMessage(message, 'Choose list options:', buttons)
        return

    if action == 'cancel':
        await query.answer()
        await editMessage(message, "List has been cancelled.")
        return

    await query.answer()
    item_type = action
    await editMessage(message, f"Searching for <code>{key}</code>...")
    await _list_drive(key, message, user_id, item_type, is_recursive)


async def drive_list(_, message):
    """
    Entry point for the GDrive list command.
    """
    if len(message.command) == 1:
        await sendMessage(message, 'Please provide a search query.')
        return

    user_id = message.from_user.id
    msg, btn = await checking_access(user_id)
    if msg:
        await sendMessage(message, msg, btn.build_menu(1) if btn else None)
        return

    buttons = await list_buttons(user_id)
    await sendMessage(message, 'Choose list options:', buttons, 'IMAGES')


bot.add_handler(MessageHandler(drive_list, filters=command(BotCommands.ListCommand) & CustomFilters.authorized & ~CustomFilters.blacklisted))
bot.add_handler(CallbackQueryHandler(select_type, filters=regex("^list_types")))
