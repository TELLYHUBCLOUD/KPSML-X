#!/usr/bin/env python3
from time import time

from bot import aria2, LOGGER
from bot.helper.ext_utils.bot_utils import EngineStatus, MirrorStatus, get_readable_time, sync_to_async


def get_download(gid):
    try:
        return aria2.get_download(gid)
    except Exception as e:
        LOGGER.error(f'{e}: Aria2c: Error while getting torrent info')
        return None


class Aria2Status:
    def __init__(self, gid, listener, seeding=False, queued=False):
        self.__gid = gid
        self.__download = get_download(gid)
        self.__listener = listener
        self.upload_details = self.__listener.upload_details
        self.queued = queued
        self.start_time = 0
        self.seeding = seeding
        self.message = self.__listener.message

    def __update(self):
        if self.__download is None:
            self.__download = get_download(self.__gid)
        else:
            self.__download = self.__download.live

        if self.__download and self.__download.followed_by_ids:
            self.__gid = self.__download.followed_by_ids[0]
            self.__download = get_download(self.__gid)

    def progress(self):
        """
        Returns the progress of the download in percentage.
        """
        return self.__download.progress_string()

    def processed_bytes(self):
        """
        Returns the processed bytes of the download.
        """
        return self.__download.completed_length_string()

    def speed(self):
        """
        Returns the download speed.
        """
        return self.__download.download_speed_string()

    def name(self):
        """
        Returns the name of the download.
        """
        return self.__download.name

    def size(self):
        """
        Returns the total size of the download.
        """
        return self.__download.total_length_string()

    def eta(self):
        """
        Returns the estimated time remaining for the download to complete.
        """
        return self.__download.eta_string()

    def listener(self):
        """
        Returns the listener object.
        """
        return self.__listener

    def status(self):
        """
        Returns the status of the download.
        """
        self.__update()
        if self.queued or (self.__download and self.__download.is_waiting):
            return MirrorStatus.STATUS_QUEUEUP if self.seeding else MirrorStatus.STATUS_QUEUEDL
        if self.__download and self.__download.is_paused:
            return MirrorStatus.STATUS_PAUSED
        if self.__download and self.__download.seeder and self.seeding:
            return MirrorStatus.STATUS_SEEDING
        return MirrorStatus.STATUS_DOWNLOADING

    def seeders_num(self):
        """
        Returns the number of seeders.
        """
        return self.__download.num_seeders

    def leechers_num(self):
        """
        Returns the number of leechers.
        """
        return self.__download.connections

    def uploaded_bytes(self):
        """
        Returns the uploaded bytes of the torrent.
        """
        return self.__download.upload_length_string()

    def upload_speed(self):
        """
        Returns the upload speed of the torrent.
        """
        self.__update()
        return self.__download.upload_speed_string()

    def ratio(self):
        """
        Returns the ratio of the torrent.
        """
        return f"{round(self.__download.upload_length / self.__download.completed_length, 3)}" if self.__download.completed_length > 0 else 0

    def seeding_time(self):
        """
        Returns the seeding time of the torrent.
        """
        return get_readable_time(time() - self.start_time)

    def download(self):
        """
        Returns the download object.
        """
        return self

    def gid(self):
        """
        Returns the GID of the download.
        """
        self.__update()
        return self.__gid

    async def cancel_download(self):
        """
        Cancels the download.
        """
        self.__update()
        if self.seeding:
            LOGGER.info(f"Cancelling seed: {self.name()}")
            await self.__listener.onUploadError(f"Seeding stopped at Ratio: {self.ratio()} and Time: {self.seeding_time()}")
            await sync_to_async(aria2.remove, [self.__download], force=True, files=True)
        else:
            if downloads := self.__download.followed_by if self.__download else None:
                downloads.append(self.__download)
                await self.__listener.onDownloadError('Download cancelled by user!')
                await sync_to_async(aria2.remove, downloads, force=True, files=True)
            else:
                msg = 'Download stopped by user!' if not self.queued else 'Task removed from queue.'
                LOGGER.info(f'Cancelling {"queued" if self.queued else ""} download: {self.name()}')
                await self.__listener.onDownloadError(msg)
                await sync_to_async(aria2.remove, [self.__download], force=True, files=True)

    def eng(self):
        """
        Returns the engine status.
        """
        return EngineStatus().STATUS_ARIA
