#!/usr/bin/env python3
from asyncio import wait_for, Event, wrap_future
from aiofiles.os import path as aiopath
from aiofiles import open as aiopen
from configparser import ConfigParser
from pyrogram.handlers import CallbackQueryHandler
from pyrogram.filters import regex, user
from functools import partial
from json import loads
from time import time

from bot import LOGGER, config_dict, bot_cache
from bot.helper.ext_utils.db_handler import DbManger
from bot.helper.telegram_helper.button_build import ButtonMaker
from bot.helper.telegram_helper.message_utils import sendMessage, editMessage, deleteMessage
from bot.helper.ext_utils.bot_utils import cmd_exec, new_thread, get_readable_file_size, new_task, get_readable_time

LIST_LIMIT = 6


@new_task
async def path_updates(client, query, obj):
    await query.answer()
    message = query.message
    data = query.data.split()

    if data[1] == 'cancel':
        obj.remote = 'Task has been cancelled!'
        obj.path = ''
        obj.is_cancelled = True
        obj.event.set()
        await deleteMessage(message)
        return

    if obj.query_proc:
        return

    obj.query_proc = True

    if data[1] == 'pre':
        obj.iter_start -= LIST_LIMIT * obj.page_step
    elif data[1] == 'nex':
        obj.iter_start += LIST_LIMIT * obj.page_step
    elif data[1] == 'back':
        if data[2] == 're':
            await obj.list_config()
        else:
            await obj.back_from_path()
    elif data[1] == 're':
        obj.remote = query.data.split(maxsplit=2)[2]
        await obj.get_path()
    elif data[1] == 'pa':
        index = int(data[3])
        obj.path = f"{obj.path}/{obj.path_list[index]['Path']}" if obj.path else obj.path_list[index]['Path']
        if data[2] == 'fo':
            await obj.get_path()
        else:
            await deleteMessage(message)
            obj.event.set()
    elif data[1] == 'ps':
        if obj.page_step == int(data[2]):
            obj.query_proc = False
            return
        obj.page_step = int(data[2])
    elif data[1] == 'root':
        obj.path = ''
        await obj.get_path()
    elif data[1] == 'itype':
        obj.item_type = data[2]
        await obj.get_path()
    elif data[1] == 'cur':
        await deleteMessage(message)
        obj.event.set()
    elif data[1] == 'def':
        path = f'{obj.remote}{obj.path}' if obj.config_path == 'wcl.conf' else f'mrcc:{obj.remote}{obj.path}'
        if path != config_dict.get('RCLONE_PATH'):
            config_dict['RCLONE_PATH'] = path
            if config_dict.get('DATABASE_URL'):
                await DbManger().update_config({'RCLONE_PATH': path})
    elif data[1] == 'owner':
        obj.config_path = 'wcl.conf'
        await obj.list_remotes()
    elif data[1] == 'user':
        obj.config_path = obj.user_rcc_path
        await obj.list_remotes()

    if data[1] not in ['pa', 'cur', 're', 'back', 'owner', 'user']:
        await obj.get_path_buttons()

    obj.query_proc = False


class RcloneList:
    def __init__(self, client, message):
        self.__user_id = message.from_user.id
        self.__rc_user = False
        self.__rc_owner = False
        self.__client = client
        self.__message = message
        self.__sections = []
        self.__reply_to = None
        self.__time = time()
        self.__timeout = 240
        self.remote = ''
        self.is_cancelled = False
        self.query_proc = False
        self.item_type = '--dirs-only'
        self.event = Event()
        self.user_rcc_path = f'wcl/{self.__user_id}.conf'
        self.config_path = ''
        self.path = ''
        self.list_status = ''
        self.path_list = []
        self.iter_start = 0
        self.page_step = 1

    @new_thread
    async def __event_handler(self):
        pfunc = partial(path_updates, obj=self)
        handler = self.__client.add_handler(CallbackQueryHandler(pfunc, filters=regex('^rcq') & user(self.__user_id)), group=-1)
        try:
            await wait_for(self.event.wait(), timeout=self.__timeout)
        except:
            self.path = ''
            self.remote = 'Timed out, task cancelled.'
            self.is_cancelled = True
            self.event.set()
        finally:
            self.__client.remove_handler(*handler)

    async def __send_list_message(self, msg, button):
        if not self.is_cancelled:
            if self.__reply_to:
                await editMessage(self.__reply_to, msg, button)
            else:
                self.__reply_to = await sendMessage(self.__message, msg, button)

    async def get_path_buttons(self):
        items_no = len(self.path_list)
        pages = (items_no + LIST_LIMIT - 1) // LIST_LIMIT
        if items_no <= self.iter_start:
            self.iter_start = 0

        buttons = ButtonMaker()
        for i, item in enumerate(self.path_list[self.iter_start:LIST_LIMIT+self.iter_start], self.iter_start):
            ptype = 'fo' if item['IsDir'] else 'fi'
            name = f"📁 {item['Path']}" if item['IsDir'] else f"[{get_readable_file_size(item['Size'])}] 📄 {item['Path']}"
            buttons.ibutton(name, f'rcq pa {ptype} {i}')

        if items_no > LIST_LIMIT:
            for i in [1, 2, 4, 6, 10, 30, 50, 100]:
                buttons.ibutton(i, f'rcq ps {i}', position='header')
            buttons.ibutton('◀️', 'rcq pre', position='footer')
            buttons.ibutton('▶️', 'rcq nex', position='footer')

        action_type = 'Download' if self.list_status == 'rcd' else 'Upload'

        if self.list_status == 'rcd':
            buttons.ibutton('Files' if self.item_type == '--dirs-only' else 'Folders', f'rcq itype {"--files-only" if self.item_type == "--dirs-only" else "--dirs-only"}', position='footer')

        if self.list_status == 'rcu' or self.path_list:
            buttons.ibutton('✅ Select Path', 'rcq cur', position='footer')

        if self.list_status == 'rcu':
            buttons.ibutton('💾 Set Default', 'rcq def', position='footer')

        if self.path or len(self.__sections) > 1 or (self.__rc_user and self.__rc_owner):
            buttons.ibutton('⬅️ Back', 'rcq back pa', position='footer')

        if self.path:
            buttons.ibutton('⏫ Root', 'rcq root', position='footer')

        buttons.ibutton('❌ Cancel', 'rcq cancel', position='footer')

        page = (self.iter_start // LIST_LIMIT) + 1
        msg = f'Choose a path for {action_type}.\n\n'
        if self.list_status == 'rcu' and (default_path := config_dict.get('RCLONE_PATH')):
            msg += f"<b>Default Path</b>: {default_path}\n"

        msg += f'<b>Items</b>: {items_no}'
        if items_no > LIST_LIMIT:
            msg += f' | <b>Page</b>: {page}/{pages} | <b>Step</b>: {self.page_step}'

        msg += f'\n<b>Type</b>: {self.item_type}\n'
        msg += f'<b>Path</b>: <code>{self.remote}{self.path}</code>\n'
        msg += f'<b>Timeout</b>: {get_readable_time(self.__timeout - (time() - self.__time))}'

        await self.__send_list_message(msg, buttons.build_menu(2))

    async def get_path(self, itype=''):
        if itype: self.item_type = itype
        elif self.list_status == 'rcu': self.item_type = '--dirs-only'

        cmd = [bot_cache['pkgs'][3], 'lsjson', self.item_type, '--fast-list', '--no-mimetype',
               '--no-modtime', '--config', self.config_path, f"{self.remote}{self.path}"]
        if self.is_cancelled: return

        res, err, code = await cmd_exec(cmd)
        if code not in [0, -9]:
            LOGGER.error(f'Rclone list error: {err} (Path: {self.remote}{self.path})')
            self.remote = err[:4000]
            self.path = ''
            self.event.set()
            return

        result = loads(res)
        if not result and itype != self.item_type and self.list_status == 'rcd':
            self.item_type = '--dirs-only' if self.item_type == '--files-only' else '--files-only'
            return await self.get_path(self.item_type)

        self.path_list = sorted(result, key=lambda x: x["Path"])
        self.iter_start = 0
        await self.get_path_buttons()

    async def list_remotes(self):
        config = ConfigParser()
        async with aiopen(self.config_path, 'r') as f:
            config.read_string(await f.read())

        self.__sections = [s for s in config.sections() if s != 'combine']

        if len(self.__sections) == 1:
            self.remote = f'{self.__sections[0]}:'
            await self.get_path()
        else:
            action_type = 'Download' if self.list_status == 'rcd' else 'Upload'
            msg = f'Choose an Rclone remote for {action_type}.\n'
            msg += f'<b>Config</b>: {self.config_path}\n'
            msg += f'<b>Timeout</b>: {get_readable_time(self.__timeout - (time() - self.__time))}'

            buttons = ButtonMaker()
            for remote in self.__sections:
                buttons.ibutton(remote, f'rcq re {remote}:')

            if self.__rc_user and self.__rc_owner:
                buttons.ibutton('⬅️ Back', 'rcq back re', position='footer')
            buttons.ibutton('❌ Cancel', 'rcq cancel', position='footer')

            await self.__send_list_message(msg, buttons.build_menu(2))

    async def list_config(self):
        if self.__rc_user and self.__rc_owner:
            action_type = 'Download' if self.list_status == 'rcd' else 'Upload'
            msg = f'Choose an Rclone config for {action_type}.\n'
            msg += f'<b>Timeout</b>: {get_readable_time(self.__timeout - (time() - self.__time))}'

            buttons = ButtonMaker()
            buttons.ibutton('👑 Owner', 'rcq owner')
            buttons.ibutton('👤 Mine', 'rcq user')
            buttons.ibutton('❌ Cancel', 'rcq cancel')
            await self.__send_list_message(msg, buttons.build_menu(2))
        else:
            self.config_path = 'wcl.conf' if self.__rc_owner else self.user_rcc_path
            await self.list_remotes()

    async def back_from_path(self):
        if self.path:
            self.path = '/'.join(self.path.split('/')[:-1])
            await self.get_path()
        elif len(self.__sections) > 1:
            await self.list_remotes()
        else:
            await self.list_config()

    async def get_rclone_path(self, status, config_path=None):
        self.list_status = status
        future = self.__event_handler()

        if config_path:
            self.config_path = config_path
            await self.list_remotes()
        else:
            self.__rc_user = await aiopath.exists(self.user_rcc_path)
            self.__rc_owner = await aiopath.exists('wcl.conf')
            if not self.__rc_owner and not self.__rc_user:
                self.event.set()
                return 'Rclone config not found!'
            await self.list_config()

        await wrap_future(future)
        await deleteMessage(self.__reply_to)

        if self.is_cancelled:
            return self.remote

        return f'mrcc:{self.remote}{self.path}' if self.config_path != 'wcl.conf' else f'{self.remote}{self.path}'
