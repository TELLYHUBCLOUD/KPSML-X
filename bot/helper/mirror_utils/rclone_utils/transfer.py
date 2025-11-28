from asyncio import create_subprocess_exec, gather
from asyncio.subprocess import PIPE
from re import findall as re_findall
from json import loads
from aiofiles.os import path as aiopath, mkdir, listdir
from aiofiles import open as aiopen
from configparser import ConfigParser
from random import randrange
from logging import getLogger

from bot import config_dict, GLOBAL_EXTENSION_FILTER, bot_cache
from bot.helper.ext_utils.bot_utils import cmd_exec, sync_to_async
from bot.helper.ext_utils.fs_utils import get_mime_type, count_files_and_folders


LOGGER = getLogger(__name__)


class RcloneTransferHelper:
    def __init__(self, listener=None, name=''):
        self.__listener = listener
        self.__proc = None
        self.__transferred_size = '0 B'
        self.__eta = '-'
        self.__percentage = '0%'
        self.__speed = '0 B/s'
        self.__size = '0 B'
        self.__is_cancelled = False
        self.__is_download = False
        self.__is_upload = False
        self.__sa_count = 1
        self.__sa_index = 0
        self.__sa_number = 0
        self.name = name

    @property
    def transferred_size(self):
        return self.__transferred_size

    @property
    def percentage(self):
        return self.__percentage

    @property
    def speed(self):
        return self.__speed

    @property
    def eta(self):
        return self.__eta

    @property
    def size(self):
        return self.__size

    async def __progress(self):
        while self.__proc and not self.__is_cancelled:
            try:
                data = (await self.__proc.stdout.readline()).decode()
                if not data: break
                if data := re_findall(r'Transferred:\s+([\d.]+\s*\w+)\s+/\s+([\d.]+\s*\w+),\s+([\d.]+%)\s*,\s+([\d.]+\s*\w+/s),\s+ETA\s+([\dwdhms]+)', data):
                    self.__transferred_size, self.__size, self.__percentage, self.__speed, self.__eta = data[0]
            except Exception:
                continue

    def __switch_service_account(self):
        if self.__sa_index == self.__sa_number - 1:
            self.__sa_index = 0
        else:
            self.__sa_index += 1
        self.__sa_count += 1
        remote = f'sa{self.__sa_index:03}'
        LOGGER.info(f"Switching to SA: {remote}")
        return remote

    async def __create_rc_sa(self, remote, remote_opts):
        sa_conf_dir = 'rclone_sa'
        sa_conf_file = f'{sa_conf_dir}/{remote}.conf'
        if await aiopath.isdir(sa_conf_dir) and await aiopath.isfile(sa_conf_file):
            return sa_conf_file

        await mkdir(sa_conf_dir, exist_ok=True)

        gd_id = remote_opts.get('team_drive') or remote_opts.get('root_folder_id')
        if not gd_id: return 'wcl.conf'

        option = 'team_drive' if 'team_drive' in remote_opts else 'root_folder_id'
        files = await listdir('accounts')
        text = ''.join(f"[sa{i:03}]\ntype = drive\nscope = drive\nservice_account_file = accounts/{sa}\n{option} = {gd_id}\n\n"
                       for i, sa in enumerate(files))

        async with aiopen(sa_conf_file, 'w') as f:
            await f.write(text)
        return sa_conf_file

    async def __start_download(self, cmd, remote_type):
        self.__proc = await create_subprocess_exec(*cmd, stdout=PIPE, stderr=PIPE)
        _, return_code = await gather(self.__progress(), self.__proc.wait())

        if self.__is_cancelled: return

        if return_code == 0:
            await self.__listener.onDownloadComplete()
        elif return_code != -9:
            error = (await self.__proc.stderr.read()).decode().strip()
            if not error and remote_type == 'drive' and config_dict.get('USE_SERVICE_ACCOUNTS'):
                error = "Service accounts might not have access to this drive."
            LOGGER.error(error)

            if self.__sa_number and remote_type == 'drive' and 'RATE_LIMIT_EXCEEDED' in error and config_dict.get('USE_SERVICE_ACCOUNTS'):
                if self.__sa_count < self.__sa_number:
                    remote = self.__switch_service_account()
                    cmd[6] = f"{remote}:{cmd[6].split(':', 1)[1]}"
                    if not self.__is_cancelled:
                        return await self.__start_download(cmd, remote_type)
                else:
                    LOGGER.info(f"Max SA switches reached: {self.__sa_count}")

            await self.__listener.onDownloadError(error[:4000])

    async def download(self, remote, rc_path, config_path, path):
        self.__is_download = True
        try:
            remote_opts = await self.__get_remote_options(config_path, remote)
        except Exception as err:
            await self.__listener.onDownloadError(str(err))
            return

        remote_type = remote_opts.get('type')
        if remote_type == 'drive' and config_dict.get('USE_SERVICE_ACCOUNTS') and config_path == 'wcl.conf' \
                and await aiopath.isdir('accounts') and not remote_opts.get('service_account_file'):
            config_path = await self.__create_rc_sa(remote, remote_opts)
            if config_path != 'wcl.conf':
                self.__sa_number = len(await listdir('accounts'))
                self.__sa_index = randrange(self.__sa_number)
                remote = f'sa{self.__sa_index:03}'
                LOGGER.info(f'Downloading with SA: {remote}')

        rcflags = self.__listener.rcFlags or config_dict.get('RCLONE_FLAGS')
        cmd = self.__get_updated_command(config_path, f'{remote}:{rc_path}', path, rcflags, 'copy')

        if remote_type == 'drive' and not rcflags:
            cmd.append('--drive-acknowledge-abuse')
        elif remote_type != 'drive':
            cmd.extend(('--retries-sleep', '3s'))

        await self.__start_download(cmd, remote_type)

    async def __get_gdrive_link(self, config_path, remote, rc_path, mime_type):
        epath = rc_path.strip('/').rsplit('/', 1)
        epath = f'{remote}:{epath[0]}' if len(epath) > 1 else f'{remote}:'
        destination = f'{remote}:{rc_path}'

        cmd = [bot_cache['pkgs'][3], 'lsjson', '--fast-list', '--no-mimetype', '--no-modtime', '--config', config_path, epath]
        res, err, code = await cmd_exec(cmd)

        if code == 0:
            result = loads(res)
            fid = next((r['ID'] for r in result if r['Path'] == self.name), None)
            return f'https://drive.google.com/drive/folders/{fid}' if mime_type == 'Folder' else f'https://drive.google.com/uc?id={fid}&export=download', destination

        LOGGER.error(f'Error getting GDrive link for {destination}: {err}')
        return '', destination

    async def __start_upload(self, cmd, remote_type):
        self.__proc = await create_subprocess_exec(*cmd, stdout=PIPE, stderr=PIPE)
        _, return_code = await gather(self.__progress(), self.__proc.wait())

        if self.__is_cancelled or return_code == -9:
            return False

        if return_code != 0:
            error = (await self.__proc.stderr.read()).decode().strip()
            if not error and remote_type == 'drive' and config_dict.get('USE_SERVICE_ACCOUNTS'):
                error = "Service accounts might not have access to this drive."
            LOGGER.error(error)

            if self.__sa_number and remote_type == 'drive' and 'RATE_LIMIT_EXCEEDED' in error and config_dict.get('USE_SERVICE_ACCOUNTS'):
                if self.__sa_count < self.__sa_number:
                    remote = self.__switch_service_account()
                    cmd[7] = f"{remote}:{cmd[7].split(':', 1)[1]}"
                    return await self.__start_upload(cmd, remote_type)
                else:
                    LOGGER.info(f"Max SA switches reached: {self.__sa_count}")

            await self.__listener.onUploadError(error[:4000])
            return False

        return True

    async def upload(self, path, size):
        self.__is_upload = True
        rc_path = self.__listener.upPath.strip('/')

        if rc_path.startswith('mrcc:'):
            rc_path = rc_path.split('mrcc:', 1)[1]
            config_path = f'wcl/{self.__listener.message.from_user.id}.conf'
        else:
            config_path = 'wcl.conf'

        remote, rc_path = rc_path.split(':', 1)

        if await aiopath.isdir(path):
            mime_type = 'Folder'
            folders, files = await count_files_and_folders(path)
            rc_path += f"/{self.name}" if rc_path else self.name
        else:
            if path.lower().endswith(tuple(GLOBAL_EXTENSION_FILTER)):
                await self.__listener.onUploadError('This file extension is excluded.')
                return
            mime_type = await sync_to_async(get_mime_type, path)
            folders, files = 0, 1

        try:
            remote_opts = await self.__get_remote_options(config_path, remote)
        except Exception as err:
            await self.__listener.onUploadError(str(err))
            return

        remote_type = remote_opts.get('type')

        if remote_type == 'drive' and config_dict.get('USE_SERVICE_ACCOUNTS') and config_path == 'wcl.conf' \
                and await aiopath.isdir('accounts') and not remote_opts.get('service_account_file'):
            fconfig_path = await self.__create_rc_sa(remote, remote_opts)
            if fconfig_path != 'wcl.conf':
                self.__sa_number = len(await listdir('accounts'))
                self.__sa_index = randrange(self.__sa_number)
                fremote = f'sa{self.__sa_index:03}'
                LOGGER.info(f'Uploading with SA: {fremote}')
        else:
            fconfig_path, fremote = config_path, remote

        rcflags = self.__listener.rcFlags or config_dict.get('RCLONE_FLAGS')
        method = 'move' if not self.__listener.seed or self.__listener.newDir else 'copy'
        cmd = self.__get_updated_command(fconfig_path, path, f'{fremote}:{rc_path}', rcflags, method)

        if remote_type == 'drive' and not rcflags:
            cmd.extend(('--drive-chunk-size', '64M', '--drive-upload-cutoff', '32M'))
        elif remote_type != 'drive':
            cmd.extend(('--retries-sleep', '3s'))

        if not await self.__start_upload(cmd, remote_type): return

        if remote_type == 'drive':
            link, destination = await self.__get_gdrive_link(config_path, remote, rc_path, mime_type)
        else:
            destination = f"{remote}:{rc_path}"
            if mime_type != 'Folder':
                destination += f'/{self.name}' if rc_path else self.name

            cmd = [bot_cache['pkgs'][3], 'link', '--config', config_path, destination]
            res, err, code = await cmd_exec(cmd)
            link = res if code == 0 else ''
            if code != 0 and code != -9:
                LOGGER.error(f'Error getting rclone link for {destination}: {err}')

        if not self.__is_cancelled:
            LOGGER.info(f'Upload finished: {destination}')
            await self.__listener.onUploadComplete(link, size, files, folders, mime_type, self.name, destination)

    @staticmethod
    def __get_updated_command(config_path, source, destination, rcflags, method):
        ext_filter = '*.{' + ','.join(GLOBAL_EXTENSION_FILTER) + '}'
        cmd = [bot_cache['pkgs'][3], method, '--fast-list', '--config', config_path, '-P', source, destination,
               '--exclude', ext_filter, '--ignore-case', '--low-level-retries', '1', '-M', '--log-file',
               'rlog.txt', '--log-level', 'DEBUG']
        if rcflags:
            for flag in rcflags.split('|'):
                if ":" in flag:
                    key, value = map(str.strip, flag.split(':', 1))
                    cmd.extend((key, value))
                elif flag:
                    cmd.append(flag.strip())
        return cmd

    @staticmethod
    async def __get_remote_options(config_path, remote):
        config = ConfigParser()
        async with aiopen(config_path, 'r') as f:
            config.read_string(await f.read())
        return {opt: config.get(remote, opt) for opt in config.options(remote)}

    async def cancel_download(self):
        self.__is_cancelled = True
        if self.__proc:
            try: self.__proc.kill()
            except: pass

        action = "Download" if self.__is_download else "Upload" if self.__is_upload else "Clone"
        LOGGER.info(f"Cancelling {action}: {self.name}")
        await self.__listener.onUploadError(f'{action} cancelled by user.')

    async def clone(self, config_path, src_remote, src_path, destination, rcflags, mime_type):
        cmd = self.__get_updated_command(config_path, f'{src_remote}:{src_path}', destination, rcflags, 'copy')

        if mime_type == 'Folder':
            folders, files = await count_files_and_folders(self.name)
        else:
            folders, files = 0, 1

        if not await self.__start_upload(cmd, 'drive'): return

        if not self.__is_cancelled:
            await self.__listener.onUploadComplete(None, self.size, files, folders, mime_type, self.name, destination)
