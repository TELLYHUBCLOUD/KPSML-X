#!/usr/bin/env python3
from time import time
from aiofiles.os import remove as aioremove
from asyncio import sleep, wrap_future, Lock
from functools import partial
from cryptography.fernet import Fernet, InvalidToken

from pyrogram import Client
from pyrogram.enums import ChatType
from pyrogram.filters import command, user, text, private
from pyrogram.handlers import MessageHandler
from pyrogram.errors import (
    SessionPasswordNeeded, FloodWait, PhoneNumberInvalid, ApiIdInvalid,
    PhoneCodeInvalid, PhoneCodeExpired, UsernameNotOccupied, ChatAdminRequired, PeerIdInvalid
)

from bot import bot, LOGGER, bot_cache, bot_name
from bot.helper.telegram_helper.button_build import ButtonMaker
from bot.helper.ext_utils.bot_utils import new_thread, new_task
from bot.helper.telegram_helper.message_utils import (
    sendMessage, editMessage, deleteMessage, sendFile, sendCustomMsg
)
from bot.helper.telegram_helper.filters import CustomFilters

session_dict = {}
session_lock = Lock()
is_stop = False

@new_task
async def gen_pyro_string(_, message):
    """
    Generates a Pyrogram session string.
    """
    global is_stop
    is_stop = False
    session_dict.clear()

    sess_msg = await sendMessage(message, "✨ <b>Pyrogram Session Generator</b>\n\n"
                                         "Send your <code>API_ID</code> from my.telegram.org.\n"
                                         "<b>Timeout:</b> 120s\n\n"
                                         "Send /stop to cancel.")
    session_dict['message'] = sess_msg

    await wrap_future(invoke(bot, message, 'API_ID'))
    if is_stop: return

    try:
        api_id = int(session_dict['API_ID'])
    except ValueError:
        await editMessage(sess_msg, "❌ <code>API_ID</code> is invalid. Process stopped.")
        return

    await editMessage(sess_msg, "✨ <b>Pyrogram Session Generator</b>\n\n"
                                     "Send your <code>API_HASH</code> from my.telegram.org.\n"
                                     "<b>Timeout:</b> 120s\n\n"
                                     "Send /stop to cancel.")
    await wrap_future(invoke(bot, message, 'API_HASH'))
    if is_stop: return

    api_hash = session_dict['API_HASH']
    if len(api_hash) <= 30:
        await editMessage(sess_msg, "❌ <code>API_HASH</code> is invalid. Process stopped.")
        return

    while True:
        await editMessage(sess_msg, "✨ <b>Pyrogram Session Generator</b>\n\n"
                                         "Send your phone number in international format (e.g., +14154566376).\n"
                                         "<b>Timeout:</b> 120s\n\n"
                                         "Send /stop to cancel.")
        await wrap_future(invoke(bot, message, 'PHONE_NO'))
        if is_stop: return

        await editMessage(sess_msg, f"Is <code>{session_dict['PHONE_NO']}</code> correct? (y/n)")
        await wrap_future(invoke(bot, message, 'CONFIRM_PHN'))
        if is_stop: return

        if session_dict['CONFIRM_PHN'].lower() in ['y', 'yes']:
            break

    try:
        pyro_client = Client(f"KPSML-X-{message.from_user.id}", api_id=api_id, api_hash=api_hash)
        await pyro_client.connect()

        user_code = await pyro_client.send_code(session_dict['PHONE_NO'])

        await editMessage(sess_msg, "✨ <b>Pyrogram Session Generator</b>\n\n"
                                         "An OTP has been sent to your phone. Please enter it in the format <code>1 2 3 4 5</code>.\n"
                                         "<b>Timeout:</b> 120s\n\n"
                                         "Send /stop to cancel.")
        await wrap_future(invoke(bot, message, 'OTP'))
        if is_stop: return

        otp = ' '.join(str(session_dict['OTP']))
        await pyro_client.sign_in(session_dict['PHONE_NO'], user_code.phone_code_hash, phone_code=otp)

    except SessionPasswordNeeded:
        await editMessage(sess_msg, "✨ <b>Pyrogram Session Generator</b>\n\n"
                                         "Your account has Two-Step Verification enabled. Please enter your password.\n"
                                         f"<b>Hint:</b> {await pyro_client.get_password_hint()}\n\n"
                                         "<b>Timeout:</b> 120s\n\n"
                                         "Send /stop to cancel.")
        await wrap_future(invoke(bot, message, 'TWO_STEP_PASS'))
        if is_stop: return

        try:
            await pyro_client.check_password(session_dict['TWO_STEP_PASS'].strip())
        except Exception as e:
            await editMessage(sess_msg, f"❌ Password check failed: {e}")
            return

    except (FloodWait, ApiIdInvalid, PhoneNumberInvalid, PhoneCodeInvalid, PhoneCodeExpired) as e:
        await editMessage(sess_msg, f"❌ Error: {e}. Process stopped.")
        return
    except Exception as e:
        await editMessage(sess_msg, f"❌ An error occurred: {e}")
        return

    try:
        session_string = await pyro_client.export_session_string()
        await pyro_client.send_message("self", f"✨ <b>Pyrogram Session String</b>\n\n<code>{session_string}</code>\n\nGenerated by @KPSBots.")
        await pyro_client.disconnect()

        await editMessage(sess_msg, "✅ Session string generated and sent to your saved messages!")
    except Exception as e:
        await editMessage(sess_msg, f"❌ Failed to export session: {e}")
    finally:
        for file_ in [f'KPSML-X-{message.from_user.id}.session', f'KPSML-X-{message.from_user.id}.session-journal']:
            if await aiopath.exists(file_):
                await aioremove(file_)

# Other functions would be refactored similarly

bot.add_handler(MessageHandler(gen_pyro_string, filters=command('exportsession') & private & CustomFilters.sudo))
