#!/usr/bin/env python3
from pyrogram.handlers import MessageHandler
from pyrogram.filters import command
from secrets import token_hex
from asyncio import sleep, gather
from aiofiles.os import path as aiopath
from cloudscraper import create_scraper as cget
from json import loads, dumps as jdumps

from bot import LOGGER, download_dict, download_dict_lock, categories_dict, config_dict, bot
from bot.helper.ext_utils.task_manager import limit_checker, task_utils
from bot.helper.mirror_utils.upload_utils.gdriveTools import GoogleDriveHelper
from bot.helper.telegram_helper.message_utils import (
    sendMessage, editMessage, deleteMessage, sendStatusMessage,
    delete_links, auto_delete_message, open_category_btns
)
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.button_build import ButtonMaker
from bot.helper.mirror_utils.status_utils.gdrive_status import GdriveStatus
from bot.helper.ext_utils.bot_utils import (
    is_gdrive_link, new_task, get_readable_file_size, sync_to_async,
    fetch_user_tds, is_share_link, is_rclone_path, cmd_exec, get_telegraph_list, arg_parser
)
from bot.helper.ext_utils.exceptions import DirectDownloadLinkException
from bot.helper.mirror_utils.download_utils.direct_link_generator import direct_link_generator
from bot.helper.mirror_utils.rclone_utils.list import RcloneList
from bot.helper.mirror_utils.rclone_utils.transfer import RcloneTransferHelper
from bot.helper.ext_utils.help_messages import CLONE_HELP_MESSAGE
from bot.helper.mirror_utils.status_utils.rclone_status import RcloneStatus
from bot.helper.listeners.tasks_listener import MirrorLeechListener
from bot.helper.themes import BotTheme


async def rcloneNode(client, message, link, dst_path, rcf, tag):
    """
    Clones a file/folder from an rclone remote to another.
    """
    if link == 'rcl':
        link = await RcloneList(client, message).get_rclone_path('rcd')
        if not is_rclone_path(link):
            await sendMessage(message, link)
            return

    config_path = f'wcl/{message.from_user.id}.conf' if link.startswith('mrcc:') else 'wcl.conf'
    link = link.split('mrcc:', 1)[1] if link.startswith('mrcc:') else link

    if not await aiopath.exists(config_path):
        await sendMessage(message, f"RClone config not found: {config_path}")
        return

    if dst_path == 'rcl' or config_dict.get('RCLONE_PATH') == 'rcl':
        dst_path = await RcloneList(client, message).get_rclone_path('rcu', config_path)
        if not is_rclone_path(dst_path):
            await sendMessage(message, dst_path)
            return

    dst_path = (dst_path or config_dict.get('RCLONE_PATH', '')).strip('/')
    if not is_rclone_path(dst_path):
        await sendMessage(message, 'Invalid RClone destination.')
        return

    if (dst_path.startswith('mrcc:') and config_path != f'wcl/{message.from_user.id}.conf') or \
       (not dst_path.startswith('mrcc:') and config_path != 'wcl.conf'):
        await sendMessage(message, 'Cannot clone between different rclone configs.')
        return

    remote, src_path = link.split(':', 1)
    src_path = src_path.strip('/')

    cmd = [bot_cache['pkgs'][3], 'lsjson', '--fast-list', '--stat', '--no-modtime', '--config', config_path, f'{remote}:{src_path}']
    res, err, code = await cmd_exec(cmd)
    if code != 0:
        await sendMessage(message, f'Rclone error: {err[:4000]}')
        return

    try:
        rstat = loads(res)
    except Exception as e:
        await sendMessage(message, f"Rclone error: {e}")
        return

    if rstat['IsDir']:
        name = src_path.rsplit('/', 1)[-1] if src_path else remote
        dst_path += name if dst_path.endswith(':') else f'/{name}'
        mime_type = 'Folder'
    else:
        name = src_path.rsplit('/', 1)[-1]
        mime_type = rstat['MimeType']

    listener = MirrorLeechListener(message, tag=tag, source_url=link)
    await listener.onDownloadStart()

    rc_transfer = RcloneTransferHelper(listener, name)
    LOGGER.info(f'Cloning: {name} from {link} to {dst_path}')
    gid = token_hex(5)

    async with download_dict_lock:
        download_dict[message.id] = RcloneStatus(rc_transfer, message, gid, 'cl', listener.upload_details)
    await sendStatusMessage(message)

    link, destination = await rc_transfer.clone(config_path, remote, src_path, dst_path, rcf, mime_type)
    if not link: return

    LOGGER.info(f'Cloning finished: {name}')

    cmd1 = [bot_cache['pkgs'][3], 'lsf', '--fast-list', '-R', '--files-only', '--config', config_path, destination]
    cmd2 = [bot_cache['pkgs'][3], 'lsf', '--fast-list', '-R', '--dirs-only', '--config', config_path, destination]
    cmd3 = [bot_cache['pkgs'][3], 'size', '--fast-list', '--json', '--config', config_path, destination]

    res1, res2, res3 = await gather(cmd_exec(cmd1), cmd_exec(cmd2), cmd_exec(cmd3))

    files = len(res1[0].split("\n"))
    folders = len(res2[0].split("\n"))
    size = loads(res3[0])['bytes']

    await listener.onUploadComplete(link, size, files, folders, mime_type, name, destination)

# GDrive clone and other functions would be refactored similarly

@new_task
async def clone(client, message):
    """
    Entry point for the clone command.
    """
    args = arg_parser(message.text.split()[1:], {
        'link': '', '-i': 0, '-up': '', '-upload': '', '-rcf': '', '-id': '',
        '-index': '', '-c': '', '-category': ''
    })

    try:
        multi = int(args['-i'])
    except:
        multi = 0

    dst_path = args['-up'] or args['-upload']
    rcf = args['-rcf']
    link = args['link']
    drive_id = args['-id']
    index_link = args['-index']
    gd_cat = args['-c'] or args['-category']
    tag = f"@{message.from_user.username}" if message.from_user.username else message.from_user.mention

    if not link and (reply_to := message.reply_to_message) and reply_to.text:
        link = reply_to.text.split('\n', 1)[0].strip()

    if not link:
        await sendMessage(message, CLONE_HELP_MESSAGE[0])
        return

    error_msg, error_button = await task_utils(message)
    if error_msg:
        await sendMessage(message, f'<b>User:</b> {tag}\n\n' + '\n'.join(error_msg), error_button.build_menu(2) if error_button else None)
        return

    if is_rclone_path(link):
        if not await aiopath.exists('wcl.conf') and not await aiopath.exists(f'wcl/{message.from_user.id}.conf'):
            await sendMessage(message, 'RClone config not found.')
            return
        if not config_dict.get('RCLONE_PATH') and not dst_path:
            await sendMessage(message, 'RClone destination not specified.')
            return
        await rcloneNode(client, message, link, dst_path, rcf, tag)
    # else:
        # GDrive clone logic would be here

bot.add_handler(MessageHandler(clone, filters=command(BotCommands.CloneCommand) & CustomFilters.authorized & ~CustomFilters.blacklisted))
