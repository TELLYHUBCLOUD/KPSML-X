#!/usr/bin/env python3
from speedtest import Speedtest, ConfigRetrievalError
from pyrogram.handlers import MessageHandler
from pyrogram.filters import command

from bot import bot, LOGGER
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.message_utils import sendMessage, deleteMessage, editMessage
from bot.helper.ext_utils.bot_utils import get_readable_file_size, new_task

@new_task
async def speedtest(_, message):
    """
    Performs a speedtest and sends the results.
    """
    status_msg = await sendMessage(message, "<i>Performing speedtest...</i>")

    try:
        test = Speedtest()
        test.get_best_server()
        test.download()
        test.upload()
        result = test.results.dict()
    except ConfigRetrievalError:
        await editMessage(status_msg, "<b>Error:</b> Could not connect to the speedtest server.")
        return
    except Exception as e:
        await editMessage(status_msg, f"<b>Error:</b> {e}")
        LOGGER.error(f"Speedtest error: {e}")
        return

    result_text = (
        f"🚀 <b>Speedtest Results</b> 🚀\n\n"
        f"<b>Upload:</b> {get_readable_file_size(result['upload'] / 8)}/s\n"
        f"<b>Download:</b> {get_readable_file_size(result['download'] / 8)}/s\n"
        f"<b>Ping:</b> {result['ping']} ms\n\n"
        f"<b>Server:</b> {result['server']['name']} ({result['server']['country']})\n"
        f"<b>ISP:</b> {result['client']['isp']} ({result['client']['ip']})"
    )

    share_img = result.get('share')

    try:
        if share_img:
            await sendMessage(message, result_text, photo=share_img)
            await deleteMessage(status_msg)
        else:
            await editMessage(status_msg, result_text)
    except Exception as e:
        LOGGER.error(f"Speedtest result sending error: {e}")
        await editMessage(status_msg, result_text)


bot.add_handler(MessageHandler(speedtest, filters=command(BotCommands.SpeedCommand) & CustomFilters.authorized & ~CustomFilters.blacklisted))
