#!/usr/bin/env python3
from pyrogram.types import InlineKeyboardMarkup 
from pyrogram.handlers import CallbackQueryHandler
from pyrogram.filters import regex
from asyncio import sleep

from bot import bot, bot_name, user_data

async def save_message(_, query):
    """
    Saves a message to the user's saved messages or a specified dump channel.
    """
    user_id = query.from_user.id
    user_dict = user_data.get(user_id, {})

    if query.data != "save":
        return

    destination_chat = user_id
    if user_dict.get('save_mode'):
        if dump_chat_id := next(iter(user_dict.get('ldump', {}).values()), None):
            destination_chat = dump_chat_id

    try:
        reply_markup = None
        if query.message.reply_markup and len(query.message.reply_markup.inline_keyboard) > 1:
            reply_markup = InlineKeyboardMarkup(query.message.reply_markup.inline_keyboard[:-1])

        await query.message.copy(destination_chat, reply_markup=reply_markup)
        await query.answer("✅ Message saved successfully!", show_alert=True)
    except Exception as e:
        error_message = "Failed to save message."
        if user_dict.get('save_mode'):
            error_message = "Could not save to dump channel. Make sure the bot is an admin with post permissions."
        else:
            await query.answer(url=f"https://t.me/{bot_name}?start=start")
            await sleep(1)
            try:
                await query.message.copy(destination_chat, reply_markup=reply_markup)
                return
            except Exception:
                pass # The error will be handled below

        await query.answer(error_message, show_alert=True)
        LOGGER.error(f"Failed to save message for user {user_id}: {e}")

bot.add_handler(CallbackQueryHandler(save_message, filters=regex(r"^save")))
