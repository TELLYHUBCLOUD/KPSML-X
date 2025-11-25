#!/usr/bin/env python3
from pathlib import Path
from traceback import format_exc
from json import JSONDecodeError
from io import BufferedReader
from re import findall as re_findall
from aiofiles.os import path as aiopath
from time import time
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
from aiohttp import ClientSession 
from aiohttp.client_exceptions import ContentTypeError

from bot import LOGGER, user_data
from bot.helper.mirror_utils.upload_utils.ddlserver.gofile import Gofile
from bot.helper.mirror_utils.upload_utils.ddlserver.streamtape import Streamtape
from bot.helper.ext_utils.fs_utils import get_mime_type


class ProgressFileReader(BufferedReader):
    def __init__(self, filename, read_callback=None):
        super().__init__(open(filename, "rb"))
        self.__read_callback = read_callback
        self.length = Path(filename).stat().st_size
        
    def read(self, size=None):
        size = size or (self.length - self.tell())
        if self.__read_callback:
            self.__read_callback(self.tell())
        return super().read(size)
        

class DDLUploader:
    def __init__(self, listener=None, name=None, path=None):
        self.name = name
        self.__processed_bytes = 0
        self.last_uploaded = 0
        self.__listener = listener
        self.__path = path
        self.__start_time = time()
        self.total_files = 0
        self.is_cancelled = False
        self.__is_errored = False
        self.__ddl_servers = {}
        self.__engine = 'DDL v1'
        self.__async_session = None
        self.__user_id = self.__listener.message.from_user.id
    
    async def __user_settings(self):
        user_dict = user_data.get(self.__user_id, {})
        self.__ddl_servers = user_dict.get('ddl_servers', {})
        
    def __progress_callback(self, current):
        chunk_size = current - self.last_uploaded
        self.last_uploaded = current
        self.__processed_bytes += chunk_size
    
    @retry(wait=wait_exponential(multiplier=2, min=4, max=8), stop=stop_after_attempt(3),
           retry=retry_if_exception_type(Exception))
    async def upload_aiohttp(self, url, file_path, req_file, data):
        with ProgressFileReader(file_path, self.__progress_callback) as file:
            data[req_file] = file
            async with ClientSession() as self.__async_session:
                async with self.__async_session.post(url, data=data) as resp:
                    if resp.status == 200:
                        try:
                            return await resp.json()
                        except (ContentTypeError, JSONDecodeError):
                            return await resp.text()
                    else:
                        LOGGER.error(f"DDL upload failed with status {resp.status}: {await resp.text()}")
                        return None

    async def __upload_to_ddl(self, file_path):
        all_links = {}
        for server, (enabled, api_key) in self.__ddl_servers.items():
            if not enabled:
                continue

            self.total_files = 0
            if server == 'gofile':
                self.__engine = 'GoFile API'
                all_links['GoFile'] = await Gofile(self, api_key).upload(file_path)
            elif server == 'streamtape':
                self.__engine = 'StreamTape API'
                try:
                    login, key = api_key.split(':')
                    all_links['StreamTape'] = await Streamtape(self, login, key).upload(file_path)
                except (ValueError, IndexError):
                    raise ValueError("StreamTape API key is not formatted correctly (should be login:key).")

            self.__processed_bytes = 0

        if not all_links:
            raise Exception("No DDL servers are enabled for upload.")

        return all_links

    async def upload(self, file_name, size):
        item_path = f"{self.__path}/{file_name}"
        LOGGER.info(f"Uploading to DDL: {item_path}")
        await self.__user_settings()

        try:
            mime_type = await get_mime_type(item_path) if await aiopath.isfile(item_path) else 'Folder'
            link = await self.__upload_to_ddl(item_path)

            if self.is_cancelled: return

            LOGGER.info(f"Successfully uploaded to DDL: {item_path}")
            await self.__listener.onUploadComplete(link, size, self.total_files, 0, mime_type, file_name)
        except Exception as err:
            LOGGER.error(f"DDL upload cancelled: {err}")
            if self.__async_session: await self.__async_session.close()
            await self.__listener.onUploadError(str(err).replace('<', '').replace('>', ''))
            self.__is_errored = True

    @property
    def speed(self):
        elapsed_time = time() - self.__start_time
        return self.__processed_bytes / elapsed_time if elapsed_time > 0 else 0

    @property
    def processed_bytes(self):
        return self.__processed_bytes
    
    @property
    def engine(self):
        return self.__engine

    async def cancel_download(self):
        self.is_cancelled = True
        LOGGER.info(f"Cancelling upload: {self.name}")
        if self.__async_session: await self.__async_session.close()
        await self.__listener.onUploadError('Upload stopped by user.')
