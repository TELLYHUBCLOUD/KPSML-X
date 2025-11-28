#!/usr/bin/env python3
from contextlib import suppress
from aiohttp import ClientSession
from urllib.parse import quote as q
from pycountry import countries as conn

from pyrogram.filters import command, regex
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from pyrogram.errors import MediaEmpty, PhotoInvalidDimensions, WebpageMediaEmpty

from bot import LOGGER, bot, config_dict
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.message_utils import sendMessage, editMessage
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.button_build import ButtonMaker

MDL_API = "http://kuryana.vercel.app/" # Public API, do not abuse

async def mydramalist_search(_, message):
    """
    Searches for dramas on MyDramaList.
    """
    if ' ' not in message.text:
        await sendMessage(message, f'Send a drama name after <code>/{BotCommands.MyDramaListCommand}</code>.')
        return

    status_msg = await sendMessage(message, '<i>Searching MyDramaList...</i>')
    title = message.text.split(' ', 1)[1]
    user_id = message.from_user.id
    buttons = ButtonMaker()

    async with ClientSession() as session, session.get(f'{MDL_API}/search/q/{q(title)}') as resp:
        if resp.status != 200:
            await editMessage(status_msg, "<i>No results found.</i>")
            return
        data = await resp.json()

    for drama in data.get('results', {}).get('dramas', []):
        buttons.ibutton(f"🎬 {drama.get('title')} ({drama.get('year')})", f"mdl {user_id} drama {drama.get('slug')}")

    buttons.ibutton("🚫 Close", f"mdl {user_id} close")
    await editMessage(status_msg, '<b>Dramas found on MyDramaList:</b>', buttons.build_menu(1))


async def extract_mdl_data(slug):
    """
    Extracts detailed information for a given drama slug.
    """
    async with ClientSession() as session, session.get(f'{MDL_API}/id/{slug}') as resp:
        if resp.status != 200:
            return None
        mdl = (await resp.json()).get("data", {})

    plot = mdl.get('synopsis', '')
    if len(plot) > 300:
        plot = f"{plot[:300]}..."

    return {
        'title': mdl.get('title'),
        'score': mdl.get('details', {}).get('score'),
        "aka": ', '.join(mdl.get("also_known_as", [])),
        'episodes': mdl.get('details', {}).get("episodes"),
        'type': mdl.get('details', {}).get("type"),
        "cast": ', '.join(f'<a href="{c.get("link")}">{c.get("name")}</a>' for c in mdl.get("casts", [])),
        "country": (conn.get(name=mdl['details'].get("country"))).flag if conn.get(name=mdl['details'].get("country")) else "",
        'aired_date': mdl.get('details', {}).get("aired", 'N/A'),
        'genres': ', '.join(f"#{g.replace(' ', '_')}" for g in mdl.get('others', {}).get("genres", [])),
        'poster': mdl.get('poster', '').replace('c.jpg?v=1', 'f.jpg?v=1').strip(),
        'synopsis': plot,
        'rating': f"{mdl.get('rating', 'N/A')} / 10",
        'url': mdl.get('link'),
    }


async def mdl_callback(_, query):
    """
    Handles callback queries for MyDramaList dramas.
    """
    message = query.message
    user_id = query.from_user.id
    data = query.data.split()

    if user_id != int(data[1]):
        await query.answer("This is not for you!", show_alert=True)
        return

    action = data[2]
    if action == "drama":
        await query.answer()
        mdl = await extract_mdl_data(data[3])
        buttons = ButtonMaker()
        buttons.ibutton("🚫 Close", f"mdl {user_id} close")

        template = config_dict.get('MDL_TEMPLATE', "No template available.")

        if mdl and template:
            caption = template.format(**mdl)
        else:
            caption = "<i>No data received.</i>"

        poster = mdl.get('poster')
        try:
            if poster:
                await message.reply_to_message.reply_photo(poster, caption=caption, reply_markup=buttons.build_menu(1))
            else:
                await sendMessage(message.reply_to_message, caption, buttons.build_menu(1))
        except (MediaEmpty, PhotoInvalidDimensions, WebpageMediaEmpty):
            poster = poster.replace('f.jpg?v=1', 'c.jpg?v=1')
            await sendMessage(message.reply_to_message, caption, buttons.build_menu(1), poster)

        await message.delete()
    else: # close
        await query.answer()
        await message.delete()
        if message.reply_to_message:
            await message.reply_to_message.delete()


bot.add_handler(MessageHandler(mydramalist_search, filters=command(BotCommands.MyDramaListCommand) & CustomFilters.authorized & ~CustomFilters.blacklisted))
bot.add_handler(CallbackQueryHandler(mdl_callback, filters=regex(r'^mdl')))
