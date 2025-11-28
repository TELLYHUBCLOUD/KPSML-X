#!/usr/bin/env python3
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from pyrogram.filters import command, regex, user
from asyncio import sleep, wait_for, Event, wrap_future
from functools import partial
from time import time

from bot import DOWNLOAD_DIR, bot, LOGGER
from bot.helper.ext_utils.task_manager import task_utils
from bot.helper.telegram_helper.message_utils import (
    sendMessage, editMessage, deleteMessage, delete_links, open_category_btns, open_dump_btns
)
from bot.helper.telegram_helper.button_build import ButtonMaker
from bot.helper.ext_utils.bot_utils import (
    get_readable_time, new_task, sync_to_async, arg_parser
)
from bot.helper.mirror_utils.download_utils.yt_dlp_download import YoutubeDLHelper, extract_info
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.listeners.tasks_listener import MirrorLeechListener
from bot.helper.ext_utils.help_messages import YT_HELP_MESSAGE


@new_task
async def select_format(_, query, obj):
    """
    Handles the callback query for format selection.
    """
    data = query.data.split()
    await query.answer()

    if data[1] == 'dict':
        await obj.qual_subbuttons(data[2])
    elif data[1] == 'mp3':
        await obj.mp3_subbuttons()
    elif data[1] == 'audio':
        await obj.audio_format()
    elif data[1] == 'aq':
        if data[2] == 'back':
            await obj.audio_format()
        else:
            await obj.audio_quality(data[2])
    elif data[1] == 'back':
        await obj.back_to_main()
    elif data[1] == 'cancel':
        await editMessage(query.message, 'Task has been cancelled.')
        obj.qual = None
        obj.is_cancelled = True
        obj.event.set()
    else:
        obj.qual = data[1] if '|' in data[1] else obj.formats.get(data[2], {}).get(data[3], [None, data[1]])[1]
        obj.event.set()


class YtSelection:
    """
    Class for selecting video/audio quality for yt-dlp downloads.
    """
    def __init__(self, client, message):
        self.__message = message
        self.__user_id = message.from_user.id
        self.__client = client
        self.__is_m4a = False
        self.__reply_to = None
        self.__time = time()
        self.__timeout = 120
        self.is_cancelled = False
        self.formats = {}
        self.qual = None
        self.event = Event()

    @new_thread
    async def __event_handler(self):
        pfunc = partial(select_format, obj=self)
        handler = self.__client.add_handler(CallbackQueryHandler(pfunc, filters=regex('^ytq') & user(self.__user_id)), group=-1)
        try:
            await wait_for(self.event.wait(), timeout=self.__timeout)
        except Exception:
            await editMessage(self.__reply_to, 'Timed out. Task cancelled.')
            self.qual = None
            self.is_cancelled = True
        finally:
            self.__client.remove_handler(*handler)

    async def get_quality(self, result):
        """
        Gets the video/audio quality from the user.
        """
        future = self.__event_handler()
        buttons = ButtonMaker()

        # ... (rest of the quality selection logic) ...

        self.__reply_to = await sendMessage(self.__message, "Choose a quality:", buttons.build_menu(2))
        await wrap_future(future)

        if not self.is_cancelled:
            await deleteMessage(self.__reply_to)

        return self.qual


@new_task
async def ytdl_leech(client, message, is_leech=False):
    """
    Handles yt-dlp mirror and leech commands.
    """
    args = arg_parser(message.text.split()[1:], {
        '-s': False, '-opt': '', '-n': '', '-up': '', '-rcf': '',
        '-id': '', '-index': '', '-c': '', '-ud': '', '-t': ''
    })

    select = args['-s']
    opt = args['-opt']
    name = args['-n']
    up = args['-up']
    rcf = args['-rcf']
    link = args['link']
    drive_id = args['-id']
    index_link = args['-index']
    gd_cat = args['-c']
    user_dump = args['-ud']
    thumb = args['-t']
    
    if not link and (reply_to := message.reply_to_message):
        link = reply_to.text.split('\n', 1)[0].strip()

    if not link:
        await sendMessage(message, YT_HELP_MESSAGE[0])
        return

    error_msg, _ = await task_utils(message)
    if error_msg:
        await sendMessage(message, f'<b>Error:</b>\n' + '\n'.join(error_msg))
        return

    listener = MirrorLeechListener(
        message, isLeech=is_leech, tag=f"@{message.from_user.username}", upPath=up,
        drive_id=drive_id, index_link=index_link, isYtdlp=True, source_url=link,
        leech_utils={'thumb': thumb}
    )

    options = {'usenetrc': True, 'cookiefile': 'cookies.txt'}
    if opt:
        # ... (option parsing logic) ...
        pass

    try:
        result = await sync_to_async(extract_info, link, options)
    except Exception as e:
        await sendMessage(message, f"Failed to extract info: {e}")
        return

    qual = None
    if not select and (qual_from_opts := options.get('format')):
        qual = qual_from_opts
    elif not select:
        qual = await YtSelection(client, message).get_quality(result)
        if not qual:
            return

    await delete_links(message)
    LOGGER.info(f'Downloading with YT-DLP: {link}')
    
    ydl = YoutubeDLHelper(listener)
    await ydl.add_download(link, f'{DOWNLOAD_DIR}{message.id}', name, qual, 'entries' in result, opt)


bot.add_handler(MessageHandler(partial(ytdl_leech, is_leech=False), filters=command(BotCommands.YtdlCommand) & CustomFilters.authorized & ~CustomFilters.blacklisted))
bot.add_handler(MessageHandler(partial(ytdl_leech, is_leech=True), filters=command(BotCommands.YtdlLeechCommand) & CustomFilters.authorized & ~CustomFilters.blacklisted))
