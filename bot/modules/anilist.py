#!/usr/bin/env python3
from requests import post as rpost
from markdown import markdown
from random import choice
from datetime import datetime
from calendar import month_name
from pycountry import countries as conn
from urllib.parse import quote as q

from bot import bot, LOGGER, config_dict, user_data
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.message_utils import sendMessage, editMessage
from bot.helper.telegram_helper.button_build import ButtonMaker
from bot.helper.ext_utils.bot_utils import get_readable_time
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from pyrogram.filters import command, regex


GENRES_EMOJI = {
    "Action": "👊", "Adventure": "ጀጀ", "Comedy": "🤣", "Drama": "🎭", "Ecchi": "💋",
    "Fantasy": "🧞", "Hentai": "🔞", "Horror": "☠️", "Mahou Shoujo": "☯️", "Mecha": "🤖",
    "Music": "🎸", "Mystery": "🔮", "Psychological": "♟️", "Romance": "💞", "Sci-Fi": "🛸",
    "Slice of Life": "☘️", "Sports": "⚽", "Supernatural": "🫧", "Thriller": "🔪"
}

ANIME_GRAPHQL_QUERY = """
query ($id: Int, $idMal: Int, $search: String) {
  Media(id: $id, idMal: $idMal, type: ANIME, search: $search) {
    id
    idMal
    title {
      romaji
      english
      native
    }
    type
    format
    status(version: 2)
    description(asHtml: false)
    startDate {
      year
      month
      day
    }
    endDate {
      year
      month
      day
    }
    season
    seasonYear
    episodes
    duration
    countryOfOrigin
    source
    hashtag
    trailer {
      id
      site
      thumbnail
    }
    updatedAt
    coverImage {
      large
    }
    bannerImage
    genres
    synonyms
    averageScore
    popularity
    favourites
    tags {
      name
      rank
    }
    relations {
      edges {
        node {
          title {
            romaji
            english
          }
          format
          status
          averageScore
          siteUrl
        }
        relationType
      }
    }
    characters {
      edges {
        role
        node {
          name {
            full
            native
          }
          siteUrl
        }
      }
    }
    studios {
      nodes {
         name
         siteUrl
      }
    }
    siteUrl
  }
}
"""
URL = 'https://graphql.anilist.co'

async def anilist(_, msg, aniid=None, u_id=None):
    if not aniid:
        user_id = msg.from_user.id
        squery = (msg.text).split(' ', 1)
        if len(squery) == 1:
            await sendMessage(msg, "Provide an AniList ID, Anime Name, or MyAnimeList ID.")
            return
        vars_ = {'search': squery[1]}
    else:
        user_id = int(u_id)
        vars_ = {'id': aniid}

    json_data = rpost(URL, json={'query': ANIME_GRAPHQL_QUERY, 'variables': vars_}).json()
    anime_resp = json_data.get('data', {}).get('Media')

    if not anime_resp:
        await sendMessage(msg, "No results found.")
        return

    ro_title = anime_resp['title']['romaji']
    na_title = anime_resp['title']['native']
    en_title = anime_resp['title']['english']
    format_ = anime_resp.get('format', 'N/A').capitalize()
    status = anime_resp.get('status', 'N/A').capitalize()
    year = anime_resp.get('seasonYear', 'N/A')

    start_date = "N/A"
    if sd := anime_resp.get('startDate'):
        if sd.get('day') and sd.get('year'):
            start_date = f"{month_name[sd['month']]} {sd['day']}, {sd['year']}"

    end_date = "N/A"
    if ed := anime_resp.get('endDate'):
        if ed.get('day') and ed.get('year'):
            end_date = f"{month_name[ed['month']]} {ed['day']}, {ed['year']}"

    season = f"{anime_resp.get('season', '').capitalize()} {year}"

    country = "N/A"
    if country_code := anime_resp.get('countryOfOrigin'):
        country_data = conn.get(alpha_2=country_code)
        country = f"{country_data.flag} {country_data.name}" if country_data else country_code

    episodes = anime_resp.get('episodes', 'N/A')
    duration = f"{get_readable_time(anime_resp['duration']*60)}" if anime_resp.get('duration') else "N/A"
    avg_score = f"{anime_resp.get('averageScore', 0)}%"
    genres = ", ".join(f"{GENRES_EMOJI.get(g, '')} #{g.replace(' ', '_')}" for g in anime_resp.get('genres', []))
    studios = ", ".join(f'<a href="{s["siteUrl"]}">{s["name"]}</a>' for s in anime_resp.get('studios', {}).get('nodes', []))
    source = anime_resp.get('source', 'N/A')
    hashtag = anime_resp.get('hashtag', 'N/A')
    synonyms = ", ".join(anime_resp.get('synonyms', []))
    site_url = anime_resp.get('siteUrl')

    trailer = None
    if trailer_data := anime_resp.get('trailer'):
        if trailer_data.get('site') == "youtube":
            trailer = f"https://youtu.be/{trailer_data.get('id')}"

    updated_at = datetime.fromtimestamp(anime_resp['updatedAt']).strftime('%d %B, %Y')
    description = anime_resp.get('description', 'N/A')
    if len(description) > 500:
        description = f"{description[:500]}..."

    popularity = anime_resp.get('popularity', 0)
    favourites = anime_resp.get('favourites', 0)
    site_id = anime_resp.get('id')
    cover_img = anime_resp.get('coverImage', {}).get('large')
    title_img = f"https://img.anili.st/media/{site_id}"

    btns = ButtonMaker()
    btns.ubutton("🎬 AniList Info", site_url, 'header')
    if trailer:
        btns.ubutton("🎞️ Trailer", trailer, 'header')
    btns.ibutton("📑 Reviews", f"anime {user_id} rev {site_id}")
    btns.ibutton("🎯 Tags", f"anime {user_id} tags {site_id}")
    btns.ibutton("🧬 Relations", f"anime {user_id} rel {site_id}")
    btns.ibutton("📊 Streaming", f"anime {user_id} sts {site_id}")
    btns.ibutton("👥 Characters", f"anime {user_id} cha {site_id}")

    user_template = user_data.get(user_id, {}).get('ani_temp') or config_dict.get('ANIME_TEMPLATE')

    try:
        template = user_template.format(**locals()).replace('<br>', '')
    except Exception as e:
        LOGGER.error(f"AniList template error: {e}")
        template = config_dict.get('ANIME_TEMPLATE', "No template available.")

    if aniid:
        return template, btns.build_menu(3)

    try:
        await sendMessage(msg, template, btns.build_menu(3), photo=title_img)
    except Exception:
        await sendMessage(msg, template, btns.build_menu(3), photo='https://te.legra.ph/file/8a5155c0fc61cc2b9728c.jpg')

async def setAnimeButtons(_, query):
    user_id = query.from_user.id
    data = query.data.split()
    site_id = data[3]

    if user_id != int(data[1]):
        await query.answer("This is not for you!", show_alert=True)
        return

    await query.answer()

    json_data = rpost(URL, json={'query': ANIME_GRAPHQL_QUERY, 'variables': {'id': site_id}}).json()
    anime_resp = json_data.get('data', {}).get('Media')

    if not anime_resp:
        await editMessage(query.message, "Anime not found.")
        return

    btns = ButtonMaker()
    btns.ibutton("⬅️ Back", f"anime {data[1]} home {site_id}")

    action = data[2]
    msg = ""

    if action == "tags":
        msg = "<b>Tags:</b>\n\n" + "\n".join(f"<a href='https://anilist.co/search/anime?genres={q(t['name'])}'>{t['name']}</a> {t['rank']}%" for t in anime_resp.get('tags', []))
    elif action == "sts":
        msg = "<b>External & Streaming Links:</b>\n\n" + "\n".join(f'<a href="{link["url"]}">{link["site"]}</a>' for link in anime_resp.get('externalLinks', []))
    elif action == "rev":
        msg = "<b>Reviews:</b>\n\n" + "\n\n".join(f'<a href="{r["siteUrl"]}">{r["summary"]}</a>\n<b>Score:</b> <code>{r["score"]} / 100</code> by <i>{r["user"]["name"]}</i>' for r in anime_resp.get('reviews', {}).get('nodes', [])[:8])
    elif action == "rel":
        msg = "<b>Relations:</b>\n\n" + "\n\n".join(
            f'<a href="{edge["node"]["siteUrl"]}">{edge["node"]["title"]["english"] or edge["node"]["title"]["romaji"]}</a>\n'
            f'<b>Format</b>: <code>{edge["node"]["format"].capitalize()}</code> | <b>Status</b>: <code>{edge["node"]["status"].capitalize()}</code>\n'
            f'<b>Score</b>: <code>{edge["node"]["averageScore"]}%</code> | <b>Relation</b>: <code>{edge.get("relationType", "N/A").capitalize()}</code>'
            for edge in anime_resp.get('relations', {}).get('edges', [])
        )
    elif action == "cha":
        msg = "<b>Characters:</b>\n\n" + "\n\n".join(
            f'• <a href="{edge["node"]["siteUrl"]}">{edge["node"]["name"]["full"]}</a> ({edge["node"]["name"]["native"]})\n'
            f'<b>Role:</b> {edge["role"].capitalize()}'
            for edge in anime_resp.get('characters', {}).get('edges', [])[:8]
        )
    elif action == "home":
        msg, btns = await anilist(None, query.message, site_id, data[1])
        await editMessage(query.message, msg, btns)
        return

    await editMessage(query.message, msg, btns.build_menu(1))

CHARACTER_GRAPHQL_QUERY = """
query ($id: Int, $search: String) {
  Character(id: $id, search: $search) {
    id
    name {
      full
      native
    }
    image {
      large
    }
    description(asHtml: false)
    siteUrl
    favourites
    media(page: 1, perPage: 8) {
      nodes {
        title {
          romaji
          english
        }
        type
        format
        siteUrl
      }
    }
  }
}
"""

MANGA_GRAPHQL_QUERY = """
query ($id: Int, $idMal: Int, $search: String) {
  Media(id: $id, idMal: $idMal, type: MANGA, search: $search) {
    id
    idMal
    title {
      romaji
      english
      native
    }
    format
    status(version: 2)
    description(asHtml: false)
    startDate {
      year
      month
      day
    }
    endDate {
      year
      month
      day
    }
    chapters
    volumes
    countryOfOrigin
    source
    updatedAt
    coverImage {
      large
    }
    bannerImage
    genres
    synonyms
    averageScore
    popularity
    favourites
    tags {
      name
    }
    relations {
      edges {
        node {
          title {
            romaji
            english
          }
        }
        relationType
      }
    }
    characters(perPage: 8) {
      nodes {
        name {
          full
        }
      }
    }
    staff {
      edges {
        role
        node {
          name {
            full
          }
        }
      }
    }
    siteUrl
  }
}
"""


async def search_character(_, msg):
    squery = msg.text.split(' ', 1)
    if len(squery) == 1:
        await sendMessage(msg, "Provide a character name.")
        return

    vars_ = {'search': squery[1]}
    json_data = rpost(URL, json={'query': CHARACTER_GRAPHQL_QUERY, 'variables': vars_}).json()
    char_resp = json_data.get('data', {}).get('Character')

    if not char_resp:
        await sendMessage(msg, "Character not found.")
        return

    description = char_resp.get('description', 'N/A').replace('~!', '').replace('!~', '')
    if len(description) > 450:
        description = f"{description[:450]}..."

    media = "\n".join(f'<b><a href="{m["siteUrl"]}">{m["title"]["english"] or m["title"]["romaji"]}</a></b> ({m["format"].capitalize()})'
                      for m in char_resp.get('media', {}).get('nodes', []))

    caption = (f'<b>{char_resp["name"]["full"]} ({char_resp["name"]["native"]})</b>\n\n'
               f'{description}\n\n'
               f'<b>Media:</b>\n{media}')

    btns = ButtonMaker()
    btns.ubutton("ℹ️ More Info", char_resp.get('siteUrl'))

    await sendMessage(msg, caption, btns.build_menu(1), photo=char_resp.get('image', {}).get('large'))


async def search_manga(_, msg):
    squery = msg.text.split(' ', 1)
    if len(squery) == 1:
        await sendMessage(msg, "Provide a manga name.")
        return

    vars_ = {'search': squery[1]}
    json_data = rpost(URL, json={'query': MANGA_GRAPHQL_QUERY, 'variables': vars_}).json()
    manga_resp = json_data.get('data', {}).get('Media')

    if not manga_resp:
        await sendMessage(msg, "Manga not found.")
        return

    ro_title = manga_resp['title']['romaji']
    na_title = manga_resp['title']['native']
    en_title = manga_resp['title']['english']
    format_ = manga_resp.get('format', 'N/A').capitalize()
    status = manga_resp.get('status', 'N/A').capitalize()

    start_date = "N/A"
    if sd := manga_resp.get('startDate'):
        if sd.get('day') and sd.get('year'):
            start_date = f"{month_name[sd['month']]} {sd['day']}, {sd['year']}"

    end_date = "N/A"
    if ed := manga_resp.get('endDate'):
        if ed.get('day') and ed.get('year'):
            end_date = f"{month_name[ed['month']]} {ed['day']}, {ed['year']}"

    country = "N/A"
    if country_code := manga_resp.get('countryOfOrigin'):
        country_data = conn.get(alpha_2=country_code)
        country = f"{country_data.flag} {country_data.name}" if country_data else country_code

    chapters = manga_resp.get('chapters', 'N/A')
    volumes = manga_resp.get('volumes', 'N/A')
    avg_score = f"{manga_resp.get('averageScore', 0)}%"
    genres = ", ".join(f"{GENRES_EMOJI.get(g, '')} #{g.replace(' ', '_')}" for g in manga_resp.get('genres', []))
    source = manga_resp.get('source', 'N/A').capitalize()
    synonyms = ", ".join(manga_resp.get('synonyms', []))

    description = manga_resp.get('description', 'N/A')
    if len(description) > 500:
        description = f"{description[:500]}..."

    caption = (f'<b>{en_title} ({ro_title})</b>\n'
               f'<b>Native:</b> {na_title}\n\n'
               f'<b>Format:</b> {format_}\n'
               f'<b>Status:</b> {status}\n'
               f'<b>Start Date:</b> {start_date}\n'
               f'<b>End Date:</b> {end_date}\n'
               f'<b>Country:</b> {country}\n'
               f'<b>Chapters:</b> {chapters}\n'
               f'<b>Volumes:</b> {volumes}\n'
               f'<b>Score:</b> {avg_score}\n'
               f'<b>Source:</b> {source}\n'
               f'<b>Genres:</b> {genres}\n'
               f'<b>Synonyms:</b> {synonyms}\n\n'
               f'<b>Description:</b>\n{description}')

    btns = ButtonMaker()
    btns.ubutton("ℹ️ More Info", manga_resp.get('siteUrl'))

    await sendMessage(msg, caption, btns.build_menu(1), photo=manga_resp.get('coverImage', {}).get('large'))


async def anime_help(_, message):
    await sendMessage(message, '<u><b>🔍 Anime Help Guide</b></u>\n\n'
                              '• /anime [AniList search]\n'
                              '• /character [AniList character search]\n'
                              '• /manga [manga search]')

bot.add_handler(MessageHandler(anilist, filters=command(BotCommands.AniListCommand) & CustomFilters.authorized & ~CustomFilters.blacklisted))
bot.add_handler(MessageHandler(search_character, filters=command(BotCommands.CharacterCommand) & CustomFilters.authorized & ~CustomFilters.blacklisted))
bot.add_handler(MessageHandler(search_manga, filters=command(BotCommands.MangaCommand) & CustomFilters.authorized & ~CustomFilters.blacklisted))
bot.add_handler(MessageHandler(anime_help, filters=command(BotCommands.AnimeHelpCommand) & CustomFilters.authorized & ~CustomFilters.blacklisted))
bot.add_handler(CallbackQueryHandler(setAnimeButtons, filters=regex(r'^anime')))
