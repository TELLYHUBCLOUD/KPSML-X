#!/usr/bin/env python3
from pyrogram.handlers import MessageHandler, EditedMessageHandler
from pyrogram.filters import command
from io import BytesIO

from bot import LOGGER, bot
from bot.helper.telegram_helper.message_utils import sendMessage, sendFile
from bot.helper.ext_utils.bot_utils import cmd_exec, new_task
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.bot_commands import BotCommands


@new_task
async def shell(_, message):
    """
    Executes a shell command.
    """
    cmd_parts = message.text.split(maxsplit=1)
    if len(cmd_parts) == 1:
        await sendMessage(message, 'No command to execute was provided.')
        return

    cmd = cmd_parts[1]
    stdout, stderr, _ = await cmd_exec(cmd, shell=True)

    reply = ""
    if stdout:
        reply += f"<b>Output:</b>\n<code>{stdout}</code>\n"
        LOGGER.info(f"Shell command '{cmd}' executed with output: {stdout}")
    if stderr:
        reply += f"<b>Error:</b>\n<code>{stderr}</code>"
        LOGGER.error(f"Shell command '{cmd}' executed with error: {stderr}")

    if len(reply) > 3000:
        with BytesIO(str.encode(reply)) as out_file:
            out_file.name = "shell_output.txt"
            await sendFile(message, out_file)
    elif reply:
        await sendMessage(message, reply)
    else:
        await sendMessage(message, 'Command executed with no output.')


bot.add_handler(MessageHandler(shell, filters=command(BotCommands.ShellCommand) & CustomFilters.sudo))
bot.add_handler(EditedMessageHandler(shell, filters=command(BotCommands.ShellCommand) & CustomFilters.sudo))
