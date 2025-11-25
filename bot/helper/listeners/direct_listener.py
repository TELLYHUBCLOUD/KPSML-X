from time import sleep

from bot import LOGGER, aria2
from bot.helper.ext_utils.bot_utils import async_to_sync, sync_to_async


class DirectListener:
    def __init__(self, foldername, total_size, path, listener, a2c_opt):
        self.__path = path
        self.__listener = listener
        self.__is_cancelled = False
        self.__a2c_opt = a2c_opt
        self.__proc_bytes = 0
        self.__failed = 0
        self.task = None
        self.name = foldername
        self.total_size = total_size
        self.is_downloading = False

    @property
    def processed_bytes(self):
        """
        Returns the total processed bytes.
        """
        if self.task:
            return self.__proc_bytes + self.task.completed_length
        return self.__proc_bytes

    @property
    def speed(self):
        """
        Returns the download speed.
        """
        return self.task.download_speed if self.task else 0

    def download(self, contents):
        """
        Starts the download of the files.
        """
        self.is_downloading = True
        for content in contents:
            if self.__is_cancelled:
                break

            self.__a2c_opt['dir'] = f"{self.__path}/{content['path']}" if content['path'] else self.__path
            self.__a2c_opt['out'] = content['filename']

            try:
                self.task = aria2.add_uris([content['url']], self.__a2c_opt, position=0)
            except Exception as e:
                self.__failed += 1
                LOGGER.error(f"Failed to download '{content['filename']}': {e}")
                continue

            self.task = self.task.live
            while not self.task.is_complete and not self.task.error_message and not self.__is_cancelled:
                sleep(1)
                self.task = self.task.live

            if self.__is_cancelled:
                self.task.remove(True, True)
                break

            if self.task.error_message:
                self.__failed += 1
                LOGGER.error(f"Failed to download '{self.task.name}': {self.task.error_message}")
                self.task.remove(True, True)
            else:
                self.__proc_bytes += self.task.total_length
                self.task.remove(True)

            self.task = None

        if self.__is_cancelled:
            return

        if self.__failed == len(contents):
            async_to_sync(self.__listener.onDownloadError, '❌ All files failed to download!')
        else:
            async_to_sync(self.__listener.onDownloadComplete)

    async def cancel_download(self):
        """
        Cancels the download.
        """
        self.__is_cancelled = True
        LOGGER.info(f"🚫 Cancelling download: {self.name}")
        await self.__listener.onDownloadError("Download cancelled by user!")
        if self.task:
            await sync_to_async(self.task.remove, force=True, files=True)
