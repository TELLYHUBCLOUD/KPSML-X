#!/usr/bin/env python3
from contextlib import suppress
from re import findall, IGNORECASE
from imdb import Cinemagoer
from pycountry import countries as conn

from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from pyrogram.filters import command, regex
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.errors import MediaEmpty, PhotoInvalidDimensions, WebpageMediaEmpty

from bot import bot, LOGGER, user_data, config_dict
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.message_utils import sendMessage, editMessage
from bot.helper.ext_utils.bot_utils import get_readable_time
from bot.helper.telegram_helper.button_build import ButtonMaker

imdb_api = Cinemagoer()

IMDB_GENRE_EMOJI = {
    "Action": "🚀", "Adult": "🔞", "Adventure": "🌋", "Animation": "🎠",
    "Biography": "📜", "Comedy": "🪗", "Crime": "🔪", "Documentary": "🎞️",
    "Drama": "🎭", "Family": "👨‍👩‍👧‍👦", "Fantasy": "🫧", "Film Noir": "🎯",
    "Game Show": "🎮", "History": "🏛️", "Horror": "🧟", "Musical": "🎻",
    "Music": "🎸", "Mystery": "🧳", "News": "📰", "Reality-TV": "🖥️",
    "Romance": "🥰", "Sci-Fi": "🌠", "Short": "📝", "Sport": "⛳",
    "Talk-Show": "👨‍🍳", "Thriller": "🗡️", "War": "⚔️", "Western": "🪩"
}
LIST_ITEMS = 4

async def imdb_search(_, message):
    """
    Searches for movies or TV series on IMDb.
    """
    if ' ' not in message.text:
        await sendMessage(message, 'Send a movie/series name or IMDb URL after the command.')
        return

    status_msg = await sendMessage(message, '<code>Searching IMDb...</code>')
    title = message.text.split(' ', 1)[1]
    user_id = message.from_user.id
    buttons = ButtonMaker()

    if title.lower().startswith("https://www.imdb.com/title/tt"):
        movie_id = title.split('/tt', 1)[1].split('/')[0]
        movie = imdb_api.get_movie(movie_id)
        if movie:
            buttons.ibutton(f"🎬 {movie.get('title')} ({movie.get('year')})", f"imdb {user_id} movie {movie_id}")
        else:
            await editMessage(status_msg, "<i>No results found.</i>")
            return
    else:
        movies = get_poster(title, bulk=True)
        if not movies:
            await editMessage(status_msg, "<i>No results found. Try again or use the IMDb Title ID.</i>")
            return
        for movie in movies:
            buttons.ibutton(f"🎬 {movie.get('title')} ({movie.get('year')})", f"imdb {user_id} movie {movie.movieID}")

    buttons.ibutton("🚫 Close", f"imdb {user_id} close")
    await editMessage(status_msg, '<b>Here\'s what I found on IMDb:</b>', buttons.build_menu(1))


def get_poster(query, bulk=False, id_only=False):
    """
    Fetches movie/series details from IMDb.
    """
    if id_only:
        movie_id = query
    else:
        query = query.strip().lower()
        title = query
        year = findall(r'[1-2]\d{3}$', query, IGNORECASE)
        if year:
            year = year[0]
            title = query.replace(year, "").strip()

        results = imdb_api.search_movie(title, results=10)
        if not results: return None

        if year:
            results = [r for r in results if str(r.get('year')) == year] or results

        results = [r for r in results if r.get('kind') in ['movie', 'tv series']] or results
        if bulk: return results
        movie_id = results[0].movieID

    movie = imdb_api.get_movie(movie_id)

    plot = movie.get('plot', ['N/A'])[0]
    if len(plot) > 300:
        plot = f"{plot[:300]}..."

    return {
        'title': movie.get('title'),
        'trailer': movie.get('videos', [None])[0],
        'votes': movie.get('votes'),
        "aka": list_to_str(movie.get("akas")),
        "seasons": movie.get("number of seasons"),
        "box_office": movie.get('box office'),
        'kind': movie.get("kind"),
        "imdb_id": f"tt{movie.get('imdbID')}",
        "cast": list_to_str(movie.get("cast")),
        "runtime": list_to_str([get_readable_time(int(r) * 60) for r in movie.get("runtimes", ["0"])]),
        "countries": list_to_hash(movie.get("countries"), flag=True),
        "certificates": list_to_str(movie.get("certificates")),
        "languages": list_to_hash(movie.get("languages")),
        "director": list_to_str(movie.get("director")),
        "writer": list_to_str(movie.get("writer")),
        "producer": list_to_str(movie.get("producer")),
        'release_date': movie.get("original air date") or movie.get('year', 'N/A'),
        'year': movie.get('year'),
        'genres': list_to_hash(movie.get("genres"), emoji=True),
        'poster': movie.get('full-size cover url'),
        'plot': plot,
        'rating': f"{movie.get('rating', 'N/A')} / 10",
        'url': f'https://www.imdb.com/title/tt{movie_id}',
    }

def list_to_str(items):
    if not items: return ""
    return ', '.join(map(str, items[:LIST_ITEMS])) + ('...' if len(items) > LIST_ITEMS else '')

def list_to_hash(items, flag=False, emoji=False):
    if not items: return ""

    def format_item(item):
        formatted = ""
        if flag:
            with suppress(AttributeError):
                formatted += f"{(conn.get(name=item)).flag} "
        if emoji:
            formatted += f"{IMDB_GENRE_EMOJI.get(item, '')} "
        return formatted + f"#{item.replace(' ', '_').replace('-', '_')}"

    return ', '.join(map(format_item, items[:LIST_ITEMS]))

# The imdb_callback function would be refactored similarly

bot.add_handler(MessageHandler(imdb_search, filters=command(BotCommands.IMDBCommand) & CustomFilters.authorized & ~CustomFilters.blacklisted))
bot.add_handler(CallbackQueryHandler(imdb_callback, filters=regex(r'^imdb')))
