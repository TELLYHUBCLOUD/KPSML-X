#!/usr/bin/env python3
from pyrogram.handlers import MessageHandler
from pyrogram.filters import command
from os import path as ospath, getcwd, chdir
from aiofiles import open as aiopen
from traceback import format_exc
from textwrap import indent
from io import StringIO, BytesIO
from re import match
from contextlib import redirect_stdout, suppress

from bot import LOGGER, bot, user
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.message_utils import sendFile, sendMessage
from bot.helper.ext_utils.bot_utils import new_task

namespaces = {}

def namespace_of(message):
    """
    Returns the namespace for a given chat.
    """
    if message.chat.id not in namespaces:
        namespaces[message.chat.id] = {
            '__builtins__': globals()['__builtins__'],
            'bot': bot,
            'message': message,
            'user': user,
        }
    return namespaces[message.chat.id]

def log_input(message):
    """
    Logs the input message.
    """
    LOGGER.info(f"INPUT: {message.text} (User: {message.from_user.id} | Chat: {message.chat.id})")

async def send_output(msg, message):
    """
    Sends the output of the evaluation or execution.
    """
    if len(str(msg)) > 2000:
        with BytesIO(str.encode(msg)) as out_file:
            out_file.name = "output.txt"
            await sendFile(message, out_file)
    else:
        LOGGER.info(f"OUTPUT: '{msg}'")
        if not msg or msg == '\n':
            msg = "Message is empty."
        elif not match(r'<(spoiler|b|i|code|s|u|a)>', msg):
            msg = f"<code>{msg}</code>"
        await sendMessage(message, msg)


@new_task
async def evaluate(_, message):
    """
    Evaluates a Python expression.
    """
    await send_output(await do_eval_exec(eval, message), message)

@new_task
async def execute(_, message):
    """
    Executes a Python statement.
    """
    await send_output(await do_eval_exec(exec, message), message)

def cleanup_code(code):
    """
    Cleans up the code to be evaluated or executed.
    """
    if code.startswith('```') and code.endswith('```'):
        return '\n'.join(code.split('\n')[1:-1])
    return code.strip('` \n')

async def do_eval_exec(func, message):
    """
    Performs the evaluation or execution.
    """
    log_input(message)
    content = message.text.split(maxsplit=1)[-1]
    body = cleanup_code(content)
    env = namespace_of(message)

    chdir(getcwd())
    async with aiopen(ospath.join(getcwd(), 'bot/modules/temp.txt'), 'w') as temp_file:
        await temp_file.write(body)

    stdout = StringIO()
    to_compile = f'async def __ex(message):\n{indent(body, "  ")}'

    try:
        exec(to_compile, env)
    except Exception as e:
        return f'{e.__class__.__name__}: {e}'

    func = env['__ex']

    try:
        with redirect_stdout(stdout):
            func_return = await func(message)
    except Exception:
        return f'{stdout.getvalue()}{format_exc()}'
    else:
        result = stdout.getvalue()
        if func_return is not None:
            result = f'{result}{func_return}'
        return result


async def clear_locals(_, message):
    """
    Clears the cached local variables for a chat.
    """
    log_input(message)
    if message.chat.id in namespaces:
        del namespaces[message.chat.id]
        await send_output("✅ Cached local variables cleared.", message)
    else:
        await send_output("🤔 No cached local variables found.", message)


bot.add_handler(MessageHandler(evaluate, filters=command(BotCommands.EvalCommand) & CustomFilters.sudo))
bot.add_handler(MessageHandler(execute, filters=command(BotCommands.ExecCommand) & CustomFilters.sudo))
bot.add_handler(MessageHandler(clear_locals, filters=command(BotCommands.ClearLocalsCommand) & CustomFilters.sudo))
