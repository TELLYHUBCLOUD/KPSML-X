#!/usr/bin/env python3
from pyrogram.filters import command
from pyrogram.handlers import MessageHandler

from bot import bot
from bot.helper.ext_utils.bot_utils import new_task
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.message_utils import sendMessage


@new_task
async def bulk_links(_, message):
    """
    A function that handles bulk links.
    """
    # Initialize format_out to a default value
    format_out = None

    if len(message.text.split()) > 1:
        format_out = message.text.split(None, 1)[1]

    if format_out:
        await sendMessage(message, f"Bulk links with format: {format_out}")
    else:
        await sendMessage(message, "No format specified for bulk links.")


bot.add_handler(MessageHandler(bulk_links, filters=command(BotCommands.BulkLinksCommand) & CustomFilters.authorized))
