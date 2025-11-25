#!/usr/bin/env python3
from traceback import format_exc
from asyncio import sleep
from aiofiles.os import remove as aioremove
from random import choice as rchoice
from time import time
from re import match as re_match
from cryptography.fernet import InvalidToken

from pyrogram import Client
from pyrogram.enums import ParseMode
from pyrogram.types import InputMediaPhoto
from pyrogram.errors import (
    ReplyMarkupInvalid, FloodWait, PeerIdInvalid, ChannelInvalid, RPCError,
    UserNotParticipant, MessageNotModified, MessageEmpty, PhotoInvalidDimensions,
    WebpageCurlFailed, MediaEmpty
)

from bot import (
    config_dict, user_data, categories_dict, bot_cache, LOGGER, bot_name,
    status_reply_dict, status_reply_dict_lock, Interval, bot, user, download_dict_lock
)
from bot.helper.ext_utils.bot_utils import (
    get_readable_message, setInterval, sync_to_async, download_image_url,
    fetch_user_tds, fetch_user_dumps, new_thread
)
from bot.helper.telegram_helper.button_build import ButtonMaker
from bot.helper.ext_utils.exceptions import TgLinkException


async def sendMessage(message, text, buttons=None, photo=None, **kwargs):
    """
    Sends a message to a chat.
    """
    try:
        if photo:
            try:
                photo = rchoice(config_dict['IMAGES']) if photo == 'IMAGES' else photo
                return await message.reply_photo(
                    photo=photo,
                    reply_to_message_id=message.id,
                    caption=text,
                    reply_markup=buttons,
                    disable_notification=True,
                    **kwargs
                )
            except (IndexError, PhotoInvalidDimensions, WebpageCurlFailed, MediaEmpty):
                des_dir = await download_image_url(photo)
                if des_dir:
                    await sendMessage(message, text, buttons, des_dir)
                    await aioremove(des_dir)
                return
            except Exception as e:
                LOGGER.error(f"Error sending photo: {format_exc()}")

        reply_to = message.reply_to_message
        return await message.reply(
            text=text,
            quote=True,
            disable_web_page_preview=True,
            disable_notification=True,
            reply_markup=buttons,
            reply_to_message_id=reply_to.id if reply_to and not (reply_to.text or reply_to.caption) else None,
            **kwargs
        )
    except FloodWait as f:
        LOGGER.warning(str(f))
        await sleep(f.value * 1.2)
        return await sendMessage(message, text, buttons, photo)
    except (ReplyMarkupInvalid, MessageEmpty):
        return await sendMessage(message, text, None, photo, parse_mode=ParseMode.DISABLED)
    except Exception as e:
        LOGGER.error(f"Error sending message: {format_exc()}")
        return str(e)


async def sendCustomMsg(chat_id, text, buttons=None, photo=None, debug=False):
    """
    Sends a custom message to a chat.
    """
    try:
        if photo:
            try:
                photo = rchoice(config_dict['IMAGES']) if photo == 'IMAGES' else photo
                return await bot.send_photo(chat_id=chat_id, photo=photo, caption=text, reply_markup=buttons, disable_notification=True)
            except (IndexError, PhotoInvalidDimensions, WebpageCurlFailed, MediaEmpty):
                des_dir = await download_image_url(photo)
                if des_dir:
                    await sendCustomMsg(chat_id, text, buttons, des_dir)
                    await aioremove(des_dir)
                return
            except Exception as e:
                LOGGER.error(f"Error sending custom photo: {format_exc()}")

        return await bot.send_message(chat_id=chat_id, text=text, disable_web_page_preview=True, disable_notification=True, reply_markup=buttons)
    except FloodWait as f:
        LOGGER.warning(str(f))
        await sleep(f.value * 1.2)
        return await sendCustomMsg(chat_id, text, buttons, photo)
    except ReplyMarkupInvalid:
        return await sendCustomMsg(chat_id, text, None, photo)
    except Exception as e:
        if debug: raise e
        LOGGER.error(f"Error sending custom message: {format_exc()}")
        return str(e)

async def editMessage(message, text, buttons=None, photo=None):
    """
    Edits a message.
    """
    try:
        if message.media:
            if photo:
                photo = rchoice(config_dict['IMAGES']) if photo == 'IMAGES' else photo
                return await message.edit_media(InputMediaPhoto(photo, text), reply_markup=buttons)
            return await message.edit_caption(caption=text, reply_markup=buttons)
        await message.edit(text=text, disable_web_page_preview=True, reply_markup=buttons)
    except FloodWait as f:
        LOGGER.warning(str(f))
        await sleep(f.value * 1.2)
        return await editMessage(message, text, buttons, photo)
    except (MessageNotModified, MessageEmpty):
        pass
    except ReplyMarkupInvalid:
        return await editMessage(message, text, None, photo)
    except Exception as e:
        LOGGER.error(f"Error editing message: {e}")
        return str(e)


async def deleteMessage(message):
    """
    Deletes a message.
    """
    try:
        await message.delete()
    except Exception as e:
        LOGGER.error(f"Error deleting message: {e}")

async def auto_delete_message(cmd_message=None, bot_message=None):
    pass

async def get_tg_link_content(link, user_id, decrypter=None):
    pass

async def open_category_btns(message):
    pass

async def delete_links(message):
    pass

async def update_all_messages(force=False):
    pass

async def sendStatusMessage(msg):
    pass

async def forcesub(message, ids, button=None):
    pass

async def user_info(user_id):
    pass

async def check_botpm(message, button=None):
    pass
