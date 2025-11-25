#!/usr/bin/env python3
from random import choice
from time import time
from copy import deepcopy
from pytz import timezone
from datetime import datetime
from urllib.parse import unquote, quote
from requests import utils as rutils
from aiofiles.os import path as aiopath, remove as aioremove, listdir, makedirs
from os import walk, path as ospath
from html import escape
from aioshutil import move
from asyncio import create_subprocess_exec, sleep, Event
from pyrogram.enums import ChatType

from bot import OWNER_ID, Interval, aria2, DOWNLOAD_DIR, download_dict, download_dict_lock, LOGGER, bot_name, DATABASE_URL, \
    MAX_SPLIT_SIZE, config_dict, status_reply_dict_lock, user_data, non_queued_up, non_queued_dl, queued_up, \
    queued_dl, queue_dict_lock, bot, GLOBAL_EXTENSION_FILTER
from bot.helper.ext_utils.bot_utils import extra_btns, sync_to_async, get_readable_file_size, get_readable_time, is_mega_link, is_gdrive_link
from bot.helper.ext_utils.fs_utils import get_base_name, get_path_size, clean_download, clean_target, \
    is_first_archive_split, is_archive, is_archive_split, join_files
from bot.helper.ext_utils.ffmpeg import edit_metadata, edit_attachment
from bot.helper.ext_utils.leech_utils import split_file, format_filename, get_document_type
from bot.helper.ext_utils.exceptions import NotSupportedExtractionArchive
from bot.helper.ext_utils.task_manager import start_from_queued
from bot.helper.mirror_utils.status_utils.extract_status import ExtractStatus
from bot.helper.mirror_utils.status_utils.zip_status import ZipStatus
from bot.helper.mirror_utils.status_utils.split_status import SplitStatus
from bot.helper.mirror_utils.status_utils.gdrive_status import GdriveStatus
from bot.helper.mirror_utils.status_utils.telegram_status import TelegramStatus
from bot.helper.mirror_utils.status_utils.ddl_status import DDLStatus
from bot.helper.mirror_utils.status_utils.rclone_status import RcloneStatus
from bot.helper.mirror_utils.status_utils.queue_status import QueueStatus
from bot.helper.mirror_utils.status_utils.metadata_status import MetadataStatus
from bot.helper.mirror_utils.status_utils.attachment_status import AttachmentStatus
from bot.helper.mirror_utils.upload_utils.gdriveTools import GoogleDriveHelper
from bot.helper.mirror_utils.upload_utils.pyrogramEngine import TgUploader
from bot.helper.mirror_utils.upload_utils.ddlEngine import DDLUploader
from bot.helper.mirror_utils.rclone_utils.transfer import RcloneTransferHelper
from bot.helper.telegram_helper.message_utils import sendCustomMsg, sendMessage, editMessage, deleteMessage, delete_all_messages, delete_links, sendMultiMessage, update_all_messages
from bot.helper.telegram_helper.button_build import ButtonMaker
from bot.helper.ext_utils.db_handler import DbManger
from bot.helper.themes import BotTheme


class MirrorLeechListener:
    def __init__(self, message, compress=False, extract=False, isQbit=False, isLeech=False, tag=None, select=False, seed=False, sameDir=None, rcFlags=None, upPath=None, isClone=False, 
                join=False, drive_id=None, index_link=None, isYtdlp=False, source_url=None, logMessage=None, leech_utils={}):
        if sameDir is None:
            sameDir = {}
        self.message = message
        self.uid = message.id
        self.excep_chat = bool(str(message.chat.id) in config_dict['EXCEP_CHATS'].split())
        self.extract = extract
        self.compress = compress
        self.isQbit = isQbit
        self.isLeech = isLeech
        self.isClone = isClone
        self.isMega = is_mega_link(source_url) if source_url else False
        self.isGdrive = is_gdrive_link(source_url) if source_url else False
        self.isYtdlp = isYtdlp
        self.tag = tag
        self.seed = seed
        self.newDir = ""
        self.dir = f"{DOWNLOAD_DIR}{self.uid}"
        self.select = select
        self.isSuperGroup = message.chat.type in [ChatType.SUPERGROUP, ChatType.CHANNEL]
        self.isPrivate = message.chat.type == ChatType.BOT
        self.user_id = self.message.from_user.id
        self.user_dict = user_data.get(self.user_id, {})
        self.isPM = config_dict['BOT_PM'] or self.user_dict.get('bot_pm')
        self.suproc = None
        self.sameDir = sameDir
        self.rcFlags = rcFlags
        self.upPath = upPath
        self.random_pic = 'IMAGES' if config_dict['IMAGES'] else None
        self.join = join
        self.drive_id = drive_id
        self.index_link = index_link
        self.logMessage = logMessage
        self.linkslogmsg = None
        self.botpmmsg = None
        self.upload_details = {}
        self.leech_utils = leech_utils
        self.source_url = (
            source_url
            if source_url and source_url.startswith('http')
            else f"https://t.me/share/url?url={source_url}"
            if source_url
            else message.link
        )
        self.source_msg = ''
        self.__setModeEng()
        self.__parseSource()

    async def clean(self):
        try:
            async with status_reply_dict_lock:
                if Interval:
                    Interval[0].cancel()
                    Interval.clear()
            await sync_to_async(aria2.purge)
            await delete_all_messages()
        except Exception:
            pass

    def __setModeEng(self):
        mode = f" #{'Leech' if self.isLeech else 'Clone' if self.isClone else 'RClone' if self.upPath not in ['gd', 'ddl'] else 'DDL' if self.upPath != 'gd' else 'GDrive'}"
        mode += ' (Zip)' if self.compress else ' (Unzip)' if self.extract else ''
        mode += f" | #{'qBit' if self.isQbit else 'ytdlp' if self.isYtdlp else 'GDrive' if (self.isClone or self.isGdrive) else 'Mega' if self.isMega else 'Aria2' if self.source_url and self.source_url != self.message.link else 'Tg'}"
        self.upload_details['mode'] = mode
        
    def __parseSource(self):
        if self.source_url == self.message.link:
            file = self.message.reply_to_message
            if file:
                self.source_url = file.link
            if file and file.media:
                mtype = file.media.value
                media = getattr(file, mtype)
                self.source_msg = f'┎ <b>Name:</b> <i>{getattr(media, "file_name", f"{mtype}_{media.file_unique_id}")}</i>\n┠ <b>Type:</b> {getattr(media, "mime_type", "image/jpeg" if mtype == "photo" else "text/plain")}\n┠ <b>Size:</b> {get_readable_file_size(media.file_size)}\n┠ <b>Created Date:</b> {media.date}\n┖ <b>Media Type:</b> {mtype.capitalize()}'
            elif file:
                self.source_msg = f"<code>{file.text}</code>"
        elif self.source_url.startswith('https://t.me/share/url?url='):
            msg = self.source_url.replace('https://t.me/share/url?url=', '')
            if msg.startswith('magnet'):
                mag = unquote(msg).split('&')
                tracCount, name, amper = 0, '', False
                for item in mag:
                    if item.startswith('tr='):
                        tracCount += 1
                    elif item.startswith('magnet:?xt=urn:btih:'):
                        hashh = item.replace('magnet:?xt=urn:btih:', '')
                    else:
                        name += ('&' if amper else '') + item.replace('dn=', '').replace('+', ' ')
                        amper = True
                self.source_msg = f"┎ <b>Name:</b> <i>{name}</i>\n┠ <b>Magnet Hash:</b> <code>{hashh}</code>\n┠ <b>Total Trackers:</b> {tracCount} \n┖ <b>Share:</b> <a href='https://t.me/share/url?url={quote(msg)}'>Share To Telegram</a>"
            else:
                self.source_msg = f"<code>{msg}</code>"
        else:
            self.source_msg = f"<code>{self.source_url}</code>"
        
    async def onDownloadStart(self):
        if config_dict['LINKS_LOG_ID'] and not self.excep_chat:
            dispTime = datetime.now(timezone(config_dict['TIMEZONE'])).strftime('%d/%m/%y, %I:%M:%S %p')
            self.linkslogmsg = await sendCustomMsg(config_dict['LINKS_LOG_ID'], BotTheme('LINKS_START', Mode=self.upload_details['mode'], Tag=self.tag) + BotTheme('LINKS_SOURCE', On=dispTime, Source=self.source_msg))
        if self.isPM and self.isSuperGroup:
            self.botpmmsg = await sendCustomMsg(self.user_id, BotTheme('PM_START', msg_link=self.source_url))
        if self.isSuperGroup and config_dict['INCOMPLETE_TASK_NOTIFIER'] and DATABASE_URL:
            await DbManger().add_incomplete_task(self.message.chat.id, self.message.link, self.tag, self.source_url, self.message.text)

    async def onDownloadComplete(self):
        multi_links = False
        while self.sameDir and (self.sameDir['total'] > 1 and len(self.sameDir['tasks']) == 1):
            await sleep(0.2)

        async with download_dict_lock:
            if self.sameDir and self.sameDir['total'] > 1:
                self.sameDir['tasks'].remove(self.uid)
                self.sameDir['total'] -= 1
                folder_name = self.sameDir['name']
                spath = f"{self.dir}/{folder_name}"
                des_path = f"{DOWNLOAD_DIR}{list(self.sameDir['tasks'])[0]}/{folder_name}"
                await makedirs(des_path, exist_ok=True)
                for item in await listdir(spath):
                    if item.endswith(('.aria2', '.!qB')):
                        continue
                    item_path = f"{spath}/{item}"
                    if item in await listdir(des_path):
                        await move(item_path, f'{des_path}/{self.uid}-{item}')
                    else:
                        await move(item_path, f'{des_path}/{item}')
                multi_links = True

            download = download_dict[self.uid]
            name = str(download.name()).replace('/', '')
            gid = download.gid()

        LOGGER.info(f"Download completed: {name}")

        if multi_links:
            await self.onUploadError('✅ Downloaded! Starting other part of the task...')
            return

        if name == "None" or self.isQbit or not await aiopath.exists(f"{self.dir}/{name}"):
            try:
                files = await listdir(self.dir)
                name = files[-1]
                if name == "yt-dlp-thumb":
                    name = files[0]
            except Exception as e:
                await self.onUploadError(str(e))
                return

        dl_path = f"{self.dir}/{name}"
        up_path = ''
        size = await get_path_size(dl_path)

        async with queue_dict_lock:
            if self.uid in non_queued_dl:
                non_queued_dl.remove(self.uid)
        await start_from_queued()

        user_dict = user_data.get(self.user_id, {})
        
        if self.join and await aiopath.isdir(dl_path):
            await join_files(dl_path)

        if self.extract:
            pswd = self.extract if isinstance(self.extract, str) else ''
            try:
                if await aiopath.isfile(dl_path):
                    up_path = get_base_name(dl_path)
                LOGGER.info(f"Extracting: {name}")
                async with download_dict_lock:
                    download_dict[self.uid] = ExtractStatus(name, size, gid, self)

                if await aiopath.isdir(dl_path):
                    if self.seed:
                        self.newDir = f"{self.dir}10000"
                        up_path = f"{self.newDir}/{name}"
                    else:
                        up_path = dl_path

                    for dirpath, _, files in await sync_to_async(walk, dl_path, topdown=False):
                        for file_ in files:
                            if is_first_archive_split(file_) or (is_archive(file_) and not file_.endswith('.rar')):
                                f_path = ospath.join(dirpath, file_)
                                t_path = dirpath.replace(self.dir, self.newDir) if self.seed else dirpath
                                cmd = ["7z", "x", f"-p{pswd}", f_path, f"-o{t_path}", "-aot", "-xr!@PaxHeader"]
                                if not pswd:
                                    del cmd[2]
                                if self.suproc == 'cancelled' or (self.suproc and self.suproc.returncode == -9):
                                    return
                                self.suproc = await create_subprocess_exec(*cmd)
                                code = await self.suproc.wait()
                                if code == -9: return
                                if code != 0: LOGGER.error('Unable to extract archive splits!')
                        if not self.seed and self.suproc and self.suproc.returncode == 0:
                            for file_ in files:
                                if is_archive_split(file_) or is_archive(file_):
                                    await aioremove(ospath.join(dirpath, file_))
                else:
                    if self.seed:
                        self.newDir = f"{self.dir}10000"
                        up_path = up_path.replace(self.dir, self.newDir)
                    cmd = ["7z", "x", f"-p{pswd}", dl_path, f"-o{up_path}", "-aot", "-xr!@PaxHeader"]
                    if not pswd:
                        del cmd[2]
                    if self.suproc == 'cancelled': return
                    self.suproc = await create_subprocess_exec(*cmd)
                    code = await self.suproc.wait()
                    if code == -9: return
                    if code == 0:
                        LOGGER.info(f"Extracted Path: {up_path}")
                        if not self.seed:
                            await aioremove(dl_path)
                    else:
                        LOGGER.error('Unable to extract archive! Uploading anyway.')
                        self.newDir = ""
                        up_path = dl_path
            except NotSupportedExtractionArchive:
                LOGGER.info("Not a valid archive, uploading file as is.")
                self.newDir = ""
                up_path = dl_path

        if metadata := self.user_dict.get('metadata') or config_dict['METADATA']:
            meta_path = up_path or dl_path
            self.newDir = f'{self.dir}10000'
            await makedirs(self.newDir, exist_ok=True)
            async with download_dict_lock:
                download_dict[self.uid] = MetadataStatus(name, size, gid, self)

            async def process_file(file_path, base_dir):
                if self.suproc == 'cancelled': return
                if (await get_document_type(file_path))[0]:
                    outfile = ospath.join(self.newDir, ospath.basename(file_path))
                    await edit_metadata(self, base_dir, file_path, outfile, metadata)

            if await aiopath.isfile(meta_path):
                await process_file(meta_path, ospath.dirname(meta_path))
            elif await aiopath.isdir(meta_path):
                for dirpath, _, files in await sync_to_async(walk, meta_path):
                    for file in files:
                        await process_file(ospath.join(dirpath, file), dirpath)
            if self.suproc == 'cancelled': return

        if attachment := self.user_dict.get("lattachment") or config_dict['ATTACHMENT']:
            attach_path = up_path or dl_path
            self.newDir = f'{self.dir}10000'
            await makedirs(self.newDir, exist_ok=True)
            async with download_dict_lock:
                download_dict[self.uid] = AttachmentStatus(name, size, gid, self)

            async def process_attachment(file_path, base_dir):
                if self.suproc == 'cancelled': return
                if (await get_document_type(file_path))[0]:
                    outfile = ospath.join(self.newDir, ospath.basename(file_path))
                    await edit_attachment(self, base_dir, file_path, outfile, attachment)

            if await aiopath.isfile(attach_path):
                await process_attachment(attach_path, ospath.dirname(attach_path))
            elif await aiopath.isdir(attach_path):
                for dirpath, _, files in await sync_to_async(walk, attach_path):
                    for file in files:
                        await process_attachment(ospath.join(dirpath, file), dirpath)
            if self.suproc == 'cancelled': return

        if self.compress:
            pswd = self.compress if isinstance(self.compress, str) else ''
            dl_path = up_path or dl_path
            up_path = f"{up_path or dl_path}.zip"
            if self.seed and self.isLeech:
                self.newDir = f"{self.dir}10000"
                up_path = f"{self.newDir}/{name}.zip"

            async with download_dict_lock:
                download_dict[self.uid] = ZipStatus(name, size, gid, self)

            LEECH_SPLIT_SIZE = user_dict.get('split_size') or config_dict['LEECH_SPLIT_SIZE']
            cmd = ["7z", f"-v{LEECH_SPLIT_SIZE}b", "a", "-mx=0", f"-p{pswd}", up_path, dl_path, *[f'-xr!*.{ext}' for ext in GLOBAL_EXTENSION_FILTER]]

            if self.isLeech and int(size) > LEECH_SPLIT_SIZE:
                if not pswd: cmd.pop(4)
                LOGGER.info(f'Zipping and splitting: {dl_path}')
            else:
                cmd.pop(1)
                if not pswd: cmd.pop(3)
                LOGGER.info(f'Zipping: {dl_path}')

            if self.suproc == 'cancelled': return
            self.suproc = await create_subprocess_exec(*cmd)
            code = await self.suproc.wait()
            if code == -9: return
            if not self.seed: await clean_target(dl_path)

        up_path = up_path or dl_path
        up_dir, up_name = ospath.split(up_path)
        size = await get_path_size(up_dir)

        if self.isLeech:
            m_size, o_files = [], []
            if not self.compress:
                LEECH_SPLIT_SIZE = user_dict.get('split_size') or config_dict['LEECH_SPLIT_SIZE']
                for dirpath, _, files in await sync_to_async(walk, up_dir, topdown=False):
                    for file_ in files:
                        f_path = ospath.join(dirpath, file_)
                        f_size = await aiopath.getsize(f_path)
                        if f_size > LEECH_SPLIT_SIZE:
                            async with download_dict_lock:
                                download_dict[self.uid] = SplitStatus(up_name, size, gid, self)
                            LOGGER.info(f"Splitting: {up_name}")
                            res = await split_file(f_path, f_size, file_, dirpath, LEECH_SPLIT_SIZE, self)
                            if not res: return
                            if res == "errored":
                                if f_size > MAX_SPLIT_SIZE: await aioremove(f_path)
                                continue
                            if not self.seed or self.newDir: await aioremove(f_path)
                            else:
                                m_size.append(f_size)
                                o_files.append(file_)

        added_to_queue = False
        if (all_limit := config_dict['QUEUE_ALL']) or (up_limit := config_dict['QUEUE_UPLOAD']):
            async with queue_dict_lock:
                dl = len(non_queued_dl)
                up = len(non_queued_up)
                if (all_limit and dl + up >= all_limit and (not up_limit or up >= up_limit)) or (up_limit and up >= up_limit):
                    added_to_queue = True
                    LOGGER.info(f"Added to upload queue: {name}")
                    event = Event()
                    queued_up[self.uid] = event

        if added_to_queue:
            async with download_dict_lock:
                download_dict[self.uid] = QueueStatus(name, size, gid, self, 'Up')
            await event.wait()
            async with download_dict_lock:
                if self.uid not in download_dict: return
            LOGGER.info(f'Starting from upload queue: {name}')

        async with queue_dict_lock:
            non_queued_up.add(self.uid)

        if self.isLeech:
            size = await get_path_size(up_dir) - sum(m_size)
            LOGGER.info(f"Leeching: {up_name}")
            tg = TgUploader(up_name, up_dir, self)
            async with download_dict_lock:
                download_dict[self.uid] = TelegramStatus(tg, size, self.message, gid, 'up', self.upload_details)
            await update_all_messages()
            await tg.upload(o_files, m_size, size)
        elif self.upPath == 'gd':
            size = await get_path_size(up_path)
            LOGGER.info(f"Uploading to GDrive: {up_name}")
            drive = GoogleDriveHelper(up_name, up_dir, self)
            async with download_dict_lock:
                download_dict[self.uid] = GdriveStatus(drive, size, self.message, gid, 'up', self.upload_details)
            await update_all_messages()
            await sync_to_async(drive.upload, up_name, size, self.drive_id)
        elif self.upPath == 'ddl':
            size = await get_path_size(up_path)
            LOGGER.info(f"Uploading to DDL: {up_name}")
            ddl = DDLUploader(self, up_name, up_dir)
            async with download_dict_lock:
                download_dict[self.uid] = DDLStatus(ddl, size, self.message, gid, self.upload_details)
            await update_all_messages()
            await ddl.upload(up_name, size)
        else:
            size = await get_path_size(up_path)
            LOGGER.info(f"Uploading to RClone: {up_name}")
            RCTransfer = RcloneTransferHelper(self, up_name)
            async with download_dict_lock:
                download_dict[self.uid] = RcloneStatus(RCTransfer, self.message, gid, 'up', self.upload_details)
            await update_all_messages()
            await RCTransfer.upload(up_path, size)

    async def onUploadComplete(self, link, size, files, folders, mime_type, name, rclonePath='', private=False):
        if self.isSuperGroup and config_dict['INCOMPLETE_TASK_NOTIFIER'] and DATABASE_URL:
            await DbManger().rm_complete_task(self.message.link)

        user_id = self.user_id
        name, _ = await format_filename(name, user_id, isMirror=not self.isLeech)

        msg = BotTheme('NAME', Name="✅ Task Completed!" if config_dict['SAFE_MODE'] and self.isSuperGroup else escape(name))
        msg += BotTheme('SIZE', Size=get_readable_file_size(size))
        msg += BotTheme('ELAPSE', Time=get_readable_time(time() - self.message.date.timestamp()))
        msg += BotTheme('MODE', Mode=self.upload_details['mode'])
        LOGGER.info(f'Task finished: {name}')
        
        buttons = ButtonMaker()
        if self.isLeech:
            msg += BotTheme('L_TOTAL_FILES', Files=folders)
            if mime_type != 0:
                msg += BotTheme('L_CORRUPTED_FILES', Corrupt=mime_type)
            msg += BotTheme('L_CC', Tag=self.tag)

            if not files:
                await sendMessage(self.message, msg, photo=self.random_pic)
            else:
                if self.source_url and config_dict['SOURCE_LINK']:
                    buttons.ubutton(BotTheme('SOURCE_URL'), self.source_url)
                if self.isSuperGroup:
                    buttons = extra_btns(buttons)[0]

                message = msg + BotTheme('L_LL_MSG') if self.isSuperGroup else msg
                if self.isSuperGroup and self.isPM:
                    message += BotTheme('L_BOT_MSG')
                    buttons.ibutton(BotTheme('CHECK_PM'), f"kpsmlx {user_id} botpm", 'header')

                f_items = [f"{i}. <a href='{link}'>{name}</a>" for i, (link, name) in enumerate(files.items(), 1)]
                fmsg = '\n'.join(f_items)

                if len((message + BotTheme('L_LL_MSG') + fmsg).encode()) < 4000:
                    if config_dict['SAVE_MSG'] and self.isSuperGroup:
                        buttons.ibutton(BotTheme('SAVE_MSG'), 'save', 'footer')
                    await sendMessage(self.message, message + BotTheme('L_LL_MSG') + fmsg, buttons.build_menu(2), photo=self.random_pic)
                else:
                    if config_dict['SAVE_MSG'] and self.isSuperGroup:
                        buttons.ibutton(BotTheme('SAVE_MSG'), 'save', 'footer')
                    await sendMessage(self.message, message, buttons.build_menu(2), photo=self.random_pic)

                    f_msgs = []
                    f_msg_chunk = ''
                    for item in f_items:
                        if len((f_msg_chunk + item + '\n').encode()) > 4000:
                            f_msgs.append(f_msg_chunk)
                            f_msg_chunk = ''
                        f_msg_chunk += item + '\n'

                    if f_msg_chunk:
                        f_msgs.append(f_msg_chunk)

                    for f_msg_part in f_msgs:
                        target_chat = self.botpmmsg or self.message if config_dict['SAFE_MODE'] else self.message
                        await sendMessage(target_chat, BotTheme('L_LL_MSG') + f_msg_part)

            if self.seed:
                if self.newDir: await clean_target(self.newDir)
                async with queue_dict_lock:
                    if self.uid in non_queued_up: non_queued_up.remove(self.uid)
                await start_from_queued()
                return
        else:
            msg += BotTheme('M_TYPE', Mimetype=mime_type)
            if mime_type == "Folder":
                msg += BotTheme('M_SUBFOLD', Folder=folders)
                msg += BotTheme('TOTAL_FILES', Files=files)

            if isinstance(link, dict):
                for dlup, dlink in link.items():
                    buttons.ubutton(BotTheme('DDL_LINK', Serv=dlup), dlink)
            elif link and (user_id == OWNER_ID or not config_dict['DISABLE_DRIVE_LINK']):
                buttons.ubutton(BotTheme('CLOUD_LINK'), link)

            if rclonePath and config_dict['RCLONE_SERVE_URL'] and not private:
                remote, path = rclonePath.split(':', 1)
                share_url = f'{config_dict["RCLONE_SERVE_URL"]}/{remote}/{rutils.quote(path)}'
                if mime_type == "Folder": share_url += '/'
                buttons.ubutton(BotTheme('RCLONE_LINK'), share_url)
            elif not rclonePath and not isinstance(link, dict):
                INDEX_URL = self.index_link or config_dict['INDEX_URL']
                if INDEX_URL:
                    share_url = f'{INDEX_URL}/{rutils.quote(name)}'
                    if mime_type == "Folder":
                        share_url += '/'
                        buttons.ubutton(BotTheme('INDEX_LINK_F'), share_url)
                    else:
                        buttons.ubutton(BotTheme('INDEX_LINK_D'), share_url)
                        if mime_type.startswith(('image', 'video', 'audio')):
                            buttons.ubutton(BotTheme('VIEW_LINK'), f'{share_url}?a=view')

            msg += BotTheme('M_CC', Tag=self.tag)
            
            if config_dict['MIRROR_LOG_ID'] and not self.excep_chat:
                log_buttons = deepcopy(buttons)
                if self.source_url and config_dict['SOURCE_LINK']:
                    log_buttons.ubutton(BotTheme('SOURCE_URL'), self.source_url)
                if config_dict['SAVE_MSG']:
                    log_buttons.ibutton(BotTheme('SAVE_MSG'), 'save', 'footer')
                log_msg = await sendMultiMessage(config_dict['MIRROR_LOG_ID'], msg, log_buttons.build_menu(2), self.random_pic)
                if self.linkslogmsg:
                    dispTime = datetime.now(timezone(config_dict['TIMEZONE'])).strftime('%d/%m/%y, %I:%M:%S %p')
                    await editMessage(self.linkslogmsg, (msg + BotTheme('LINKS_SOURCE', On=dispTime, Source=self.source_msg) + BotTheme('L_LL_MSG') + f"\n\n<a href='{log_msg.values[0].link}'>{escape(name)}</a>"))
            
            if self.isPM and self.isSuperGroup:
                msg += BotTheme('M_BOT_MSG')

            buttons = extra_btns(buttons)[0]
            if self.source_url and config_dict['SOURCE_LINK'] and (not self.isSuperGroup or not config_dict['SAFE_MODE']):
                buttons.ubutton(BotTheme('SOURCE_URL'), self.source_url)
            if config_dict['SAVE_MSG'] and self.isSuperGroup:
                buttons.ibutton(BotTheme('SAVE_MSG'), 'save', 'footer')

            await sendMessage(self.message, msg, buttons.build_menu(2), photo=self.random_pic)

            if self.seed:
                if self.newDir: await clean_target(self.newDir)
                elif self.compress: await clean_target(f"{self.dir}/{name}")
                async with queue_dict_lock:
                    if self.uid in non_queued_up: non_queued_up.remove(self.uid)
                await start_from_queued()
                return
        
        if self.botpmmsg and (not config_dict['DELETE_LINKS'] or config_dict['CLEAN_LOG_MSG']):
            await deleteMessage(self.botpmmsg)
        
        await clean_download(self.dir)
        async with download_dict_lock:
            if self.uid in download_dict: del download_dict[self.uid]
            if len(download_dict) == 0: await self.clean()
            else: await update_all_messages()

        async with queue_dict_lock:
            if self.uid in non_queued_up: non_queued_up.remove(self.uid)

        await start_from_queued()
        await delete_links(self.message)

    async def onDownloadError(self, error, button=None):
        async with download_dict_lock:
            if self.uid in download_dict:
                del download_dict[self.uid]
            if len(download_dict) == 0: await self.clean()
            else: await update_all_messages()
            if self.sameDir and self.uid in self.sameDir['tasks']:
                self.sameDir['tasks'].remove(self.uid)
                self.sameDir['total'] -= 1

        msg = f'''<b>❌ Download Stopped!</b>
┠ <b>Task for:</b> {self.tag}
┠ <b>Due To:</b> {escape(error)}
┠ <b>Mode:</b> {self.upload_details['mode']}
┖ <b>Elapsed:</b> {get_readable_time(time() - self.message.date.timestamp())}'''
        await sendMessage(self.message, msg, button)

        if self.isSuperGroup and config_dict['INCOMPLETE_TASK_NOTIFIER'] and DATABASE_URL:
            await DbManger().rm_complete_task(self.message.link)

        async with queue_dict_lock:
            for q_dict in [queued_dl, queued_up, non_queued_dl, non_queued_up]:
                if self.uid in q_dict:
                    if isinstance(q_dict, dict): q_dict[self.uid].set()
                    q_dict.remove(self.uid)

        await start_from_queued()
        await sleep(3)
        await clean_download(self.dir)
        if self.newDir: await clean_download(self.newDir)

    async def onUploadError(self, error):
        async with download_dict_lock:
            if self.uid in download_dict:
                del download_dict[self.uid]
            if len(download_dict) == 0: await self.clean()
            else: await update_all_messages()

        msg = f'''<b>❌ Upload Stopped!</b>
┠ <b>Task for:</b> {self.tag}
┠ <b>Due To:</b> {escape(error)}
┠ <b>Mode:</b> {self.upload_details['mode']}
┖ <b>Elapsed:</b> {get_readable_time(time() - self.message.date.timestamp())}'''
        await sendMessage(self.message, msg)

        if self.isSuperGroup and config_dict['INCOMPLETE_TASK_NOTIFIER'] and DATABASE_URL:
            await DbManger().rm_complete_task(self.message.link)

        async with queue_dict_lock:
            for q_dict in [queued_dl, queued_up, non_queued_dl, non_queued_up]:
                if self.uid in q_dict:
                    if isinstance(q_dict, dict): q_dict[self.uid].set()
                    q_dict.remove(self.uid)

        await start_from_queued()
        await sleep(3)
        await clean_download(self.dir)
        if self.newDir: await clean_download(self.newDir)
