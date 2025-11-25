#!/usr/bin/env python3
from bot import LOGGER
from bot.helper.ext_utils.bot_utils import EngineStatus, get_readable_file_size, MirrorStatus


class QueueStatus:
    def __init__(self, name, size, gid, listener, status):
        self.__name = name
        self.__size = size
        self.__gid = gid
        self.__listener = listener
        self.upload_details = listener.upload_details
        self.__status = status
        self.message = listener.message

    def gid(self):
        """
        Returns the GID of the download.
        """
        return self.__gid

    def name(self):
        """
        Returns the name of the download.
        """
        return self.__name

    def size(self):
        """
        Returns the total size of the download.
        """
        return get_readable_file_size(self.__size)

    def status(self):
        """
        Returns the status of the download.
        """
        return MirrorStatus.STATUS_QUEUEDL if self.__status == 'dl' else MirrorStatus.STATUS_QUEUEUP

    def processed_bytes(self):
        """
        Returns the processed bytes of the download.
        """
        return 0

    def progress(self):
        """
        Returns the progress of the download in percentage.
        """
        return '0%'

    def speed(self):
        """
        Returns the speed of the download.
        """
        return '0B/s'

    def eta(self):
        """
        Returns the estimated time remaining for the download to complete.
        """
        return '-'

    def download(self):
        """
        Returns the download object.
        """
        return self

    async def cancel_download(self):
        """
        Cancels the download.
        """
        LOGGER.info(f'Cancelling queued {"download" if self.__status == "dl" else "upload"}: {self.__name}')
        if self.__status == 'dl':
            await self.__listener.onDownloadError('Task removed from download queue.')
        else:
            await self.__listener.onUploadError('Task removed from upload queue.')

    def eng(self):
        """
        Returns the engine status.
        """
        return EngineStatus().STATUS_QUEUE
