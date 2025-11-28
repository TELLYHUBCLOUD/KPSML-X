#!/usr/bin/env python3
from asyncio import sleep
from aiofiles.os import path as aiopath, remove as aioremove, mkdir
from telegraph import upload_file

from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from pyrogram.filters import command, regex

from bot import bot, LOGGER, config_dict, DATABASE_URL
from bot.helper.telegram_helper.message_utils import sendMessage, editMessage, deleteMessage
from bot.helper.ext_utils.bot_utils import handleIndex, new_task
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.ext_utils.db_handler import DbManger
from bot.helper.telegram_helper.button_build import ButtonMaker

@new_task
async def picture_add(_, message):
    """
    Adds an image to the bot's image list.
    """
    reply = message.reply_to_message
    status_msg = await sendMessage(message, "<i>Fetching input...</i>")

    pic_add = None
    if len(message.command) > 1 or (reply and reply.text):
        msg_text = reply.text if reply else message.command[1]
        if not msg_text.startswith("http"):
            await editMessage(status_msg, "<b>Please provide a valid link starting with 'http'.</b>")
            return
        pic_add = msg_text.strip()
        await editMessage(status_msg, f"<b>Adding your link:</b> <code>{pic_add}</code>")

    elif reply and reply.photo:
        if reply.photo.file_size > 10485760: # 10MB
            await editMessage(status_msg, "<i>Image size is too large (max 10MB).</i>")
            return
        try:
            photo_dir = await reply.download()
            await editMessage(status_msg, "<b>Uploading to graph.org...</b>")
            pic_add = f'https://graph.org{upload_file(photo_dir)[0]}'
        except Exception as e:
            LOGGER.error(f"Images Error: {e}")
            await editMessage(status_msg, str(e))
        finally:
            if 'photo_dir' in locals() and await aiopath.exists(photo_dir):
                await aioremove(photo_dir)
    else:
        help_msg = (f"<b>Usage:</b>\n"
                    f"Reply to a link or photo with <code>/{BotCommands.AddImageCommand}</code>.\n"
                    f"Or use <code>/{BotCommands.AddImageCommand} [link]</code>.")
        await editMessage(status_msg, help_msg)
        return

    if pic_add:
        config_dict.setdefault('IMAGES', []).append(pic_add)
        if DATABASE_URL:
            await DbManger().update_config({'IMAGES': config_dict['IMAGES']})
        await editMessage(status_msg, f"<b>✅ Image added successfully!</b>\n\n<b>Total Images:</b> {len(config_dict['IMAGES'])}")


async def pictures(_, message):
    """
    Displays the bot's image gallery.
    """
    if not config_dict.get('IMAGES'):
        await sendMessage(message, f"<b>No images found!</b> Add one with <code>/{BotCommands.AddImageCommand}</code>.")
        return

    status_msg = await sendMessage(message, "<i>Generating image gallery...</i>")

    buttons = ButtonMaker()
    user_id = message.from_user.id
    buttons.ibutton("◀️", f"images {user_id} turn -1")
    buttons.ibutton("▶️", f"images {user_id} turn 1")
    buttons.ibutton("🗑️ Remove", f"images {user_id} remov 0")
    buttons.ibutton("❌ Close", f"images {user_id} close")
    buttons.ibutton("⚠️ Remove All", f"images {user_id} removall", 'footer')

    await deleteMessage(status_msg)
    await sendMessage(message, f'<b>Image 1 / {len(config_dict["IMAGES"])}</b>', buttons.build_menu(2), config_dict['IMAGES'][0])


@new_task
async def pics_callback(_, query):
    """
    Handles callback queries for the image gallery.
    """
    message = query.message
    user_id = query.from_user.id
    data = query.data.split()

    if user_id != int(data[1]):
        await query.answer("This is not for you!", show_alert=True)
        return

    action = data[2]

    if action == "turn":
        await query.answer()
        new_index = handleIndex(int(data[3]), config_dict['IMAGES'])
        total_images = len(config_dict['IMAGES'])

        buttons = ButtonMaker()
        buttons.ibutton("◀️", f"images {user_id} turn {new_index-1}")
        buttons.ibutton("▶️", f"images {user_id} turn {new_index+1}")
        buttons.ibutton("🗑️ Remove", f"images {user_id} remov {new_index}")
        buttons.ibutton("❌ Close", f"images {user_id} close")
        buttons.ibutton("⚠️ Remove All", f"images {user_id} removall", 'footer')

        await editMessage(message, f'<b>Image {new_index+1} / {total_images}</b>', buttons.build_menu(2), config_dict['IMAGES'][new_index])

    elif action == "remov":
        index_to_remove = int(data[3])
        config_dict['IMAGES'].pop(index_to_remove)
        if DATABASE_URL:
            await DbManger().update_config({'IMAGES': config_dict['IMAGES']})
        await query.answer("Image removed successfully.", show_alert=True)

        if not config_dict['IMAGES']:
            await deleteMessage(message)
            await sendMessage(message, f"<b>No images left!</b> Add one with <code>/{BotCommands.AddImageCommand}</code>.")
            return

        await pics_callback(_, query) # Refresh the gallery

    elif action == 'removall':
        config_dict['IMAGES'].clear()
        if DATABASE_URL:
            await DbManger().update_config({'IMAGES': {}})
        await query.answer("All images have been removed.", show_alert=True)
        await deleteMessage(message)

    else: # close
        await query.answer()
        await deleteMessage(message)
        if message.reply_to_message:
            await deleteMessage(message.reply_to_message)


bot.add_handler(MessageHandler(picture_add, filters=command(BotCommands.AddImageCommand) & CustomFilters.authorized & ~CustomFilters.blacklisted))
bot.add_handler(MessageHandler(pictures, filters=command(BotCommands.ImagesCommand) & CustomFilters.authorized & ~CustomFilters.blacklisted))
bot.add_handler(CallbackQueryHandler(pics_callback, filters=regex(r'^images')))
