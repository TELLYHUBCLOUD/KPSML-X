#!/usr/bin/env python3
from aiohttp import ClientSession
from re import search as re_search
from shlex import split as ssplit
from aiofiles import open as aiopen
from aiofiles.os import remove as aioremove, path as aiopath, mkdir
from os import path as ospath, getcwd

from pyrogram.handlers import MessageHandler
from pyrogram.filters import command

from bot import LOGGER, bot, config_dict
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.message_utils import editMessage, sendMessage
from bot.helper.ext_utils.bot_utils import cmd_exec
from bot.helper.ext_utils.telegraph_helper import telegraph


async def gen_mediainfo(message, link=None, media=None, mmsg=None):
    """
    Generates MediaInfo for a given file or link.
    """
    status_msg = await sendMessage(message, '<i>Generating MediaInfo...</i>')

    path = "Mediainfo/"
    if not await aiopath.isdir(path):
        await mkdir(path)

    des_path = ""
    try:
        if link:
            filename = re_search(r'/(.+)$', link).group(1)
            des_path = ospath.join(path, filename)
            headers = {"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36"}
            async with ClientSession() as session, session.get(link, headers=headers) as response, aiopen(des_path, "wb") as f:
                async for chunk in response.content.iter_chunked(10000000):
                    await f.write(chunk)
                    break
        elif media:
            des_path = ospath.join(path, media.file_name)
            if media.file_size <= 50000000:
                await mmsg.download(ospath.join(getcwd(), des_path))
            else:
                async for chunk in bot.stream_media(media, limit=5):
                    async with aiopen(des_path, "ab") as f:
                        await f.write(chunk)

        stdout, _, _ = await cmd_exec(ssplit(f'mediainfo "{des_path}"'))

        if stdout:
            tc = f"<h4>{ospath.basename(des_path)}</h4><br><br>{parse_info(stdout)}"
            link_id = (await telegraph.create_page(title='MediaInfo', content=tc))["path"]
            await status_msg.edit(f"<b>MediaInfo:</b>\n\n🔗 https://graph.org/{link_id}", disable_web_page_preview=False)
        else:
            await editMessage(status_msg, "Failed to generate MediaInfo.")

    except Exception as e:
        LOGGER.error(f"MediaInfo error: {e}")
        await editMessage(status_msg, f"MediaInfo generation failed: {e}")
    finally:
        if await aiopath.exists(des_path):
            await aioremove(des_path)

SECTION_DICT = {'General': '🗒️', 'Video': '🎞️', 'Audio': '🔊', 'Text': '🔠', 'Menu': '🗃️'}
def parse_info(out):
    """
    Parses the MediaInfo output into a formatted string.
    """
    tc = ''
    trigger = False
    for line in out.split('\n'):
        for section, emoji in SECTION_DICT.items():
            if line.startswith(section):
                trigger = True
                if section != 'General': tc += '</pre><br>'
                tc += f"<h4>{emoji} {line.replace('Text', 'Subtitle')}</h4>"
                break
        if trigger:
            tc += '<br><pre>'
            trigger = False
        else:
            tc += f"{line}\n"
    tc += '</pre><br>'
    return tc


async def mediainfo(_, message):
    """
    Entry point for the mediainfo command.
    """
    reply = message.reply_to_message
    help_msg = (
        "<b>Usage:</b>\n"
        f"Reply to a media file with <code>/{BotCommands.MediaInfoCommand[0]}</code>.\n\n"
        "<b>Or provide a download link:</b>\n"
        f"<code>/{BotCommands.MediaInfoCommand[0]} [link]</code>"
    )

    if len(message.command) > 1 or (reply and reply.text):
        link = reply.text if reply else message.command[1]
        await gen_mediainfo(message, link)
    elif reply:
        media_obj = next((m for m in [reply.document, reply.video, reply.audio, reply.voice, reply.animation, reply.video_note] if m), None)
        if media_obj:
            await gen_mediainfo(message, None, media_obj, reply)
        else:
            await sendMessage(message, help_msg)
    else:
        await sendMessage(message, help_msg)

bot.add_handler(MessageHandler(mediainfo, filters=command(BotCommands.MediaInfoCommand) & CustomFilters.authorized & ~CustomFilters.blacklisted))
