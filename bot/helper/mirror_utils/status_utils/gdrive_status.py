#!/usr/bin/env python3
from bot.helper.ext_utils.bot_utils import EngineStatus, MirrorStatus, get_readable_file_size, get_readable_time


class GdriveStatus:
    def __init__(self, obj, size, message, gid, status, upload_details):
        self.__obj = obj
        self.__size = size
        self.__gid = gid
        self.__status = status
        self.upload_details = upload_details
        self.message = message

    def processed_bytes(self):
        """
        Returns the processed bytes of the download/upload.
        """
        return get_readable_file_size(self.__obj.processed_bytes)

    def size(self):
        """
        Returns the total size of the download/upload.
        """
        return get_readable_file_size(self.__size)

    def status(self):
        """
        Returns the status of the download/upload.
        """
        if self.__status == 'up':
            return MirrorStatus.STATUS_UPLOADING
        if self.__status == 'dl':
            return MirrorStatus.STATUS_DOWNLOADING
        return MirrorStatus.STATUS_CLONING

    def name(self):
        """
        Returns the name of the file/folder.
        """
        return self.__obj.name

    def gid(self) -> str:
        """
        Returns the GID of the download/upload.
        """
        return self.__gid

    def progress_raw(self):
        """
        Returns the progress of the download/upload in raw format.
        """
        try:
            return self.__obj.processed_bytes / self.__size * 100
        except ZeroDivisionError:
            return 0

    def progress(self):
        """
        Returns the progress of the download/upload in percentage.
        """
        return f'{round(self.progress_raw(), 2)}%'

    def speed(self):
        """
        Returns the speed of the download/upload.
        """
        return f'{get_readable_file_size(self.__obj.speed)}/s'

    def eta(self):
        """
        Returns the estimated time remaining for the download/upload to complete.
        """
        try:
            seconds = (self.__size - self.__obj.processed_bytes) / self.__obj.speed
            return get_readable_time(seconds)
        except:
            return '-'

    def download(self):
        """
        Returns the download object.
        """
        return self.__obj

    def eng(self):
        """
        Returns the engine status.
        """
        return EngineStatus().STATUS_GD
