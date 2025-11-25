#!/usr/bin/env python3
from os import walk, path as ospath
from aiofiles.os import remove as aioremove, path as aiopath, listdir, rmdir, makedirs
from aioshutil import rmtree as aiormtree
from shutil import rmtree, disk_usage
from magic import Magic
from re import split as re_split, I, search as re_search
from subprocess import run as srun
from sys import exit as sexit

from .exceptions import NotSupportedExtractionArchive
from bot import bot_cache, aria2, LOGGER, DOWNLOAD_DIR, get_client, GLOBAL_EXTENSION_FILTER
from bot.helper.ext_utils.bot_utils import sync_to_async, cmd_exec

ARCH_EXT = [".tar.bz2", ".tar.gz", ".bz2", ".gz", ".tar.xz", ".tar", ".tbz2", ".tgz", ".lzma2",
            ".zip", ".7z", ".z", ".rar", ".iso", ".wim", ".cab", ".apm", ".arj", ".chm",
            ".cpio", ".cramfs", ".deb", ".dmg", ".fat", ".hfs", ".lzh", ".lzma", ".mbr",
            ".msi", ".mslz", ".nsis", ".ntfs", ".rpm", ".squashfs", ".udf", ".vhd", ".xar"]

FIRST_SPLIT_REGEX = r'(\.|_)part0*1\.rar$|(\.|_)7z\.0*1$|(\.|_)zip\.0*1$|^(?!.*(\.|_)part\d+\.rar$).*\.rar$'

SPLIT_REGEX = r'\.r\d+$|\.7z\.\d+$|\.z\d+$|\.zip\.\d+$'


def is_first_archive_split(file):
    """
    Checks if a file is the first part of a split archive.
    """
    return bool(re_search(FIRST_SPLIT_REGEX, file))


def is_archive(file):
    """
    Checks if a file is an archive.
    """
    return file.endswith(tuple(ARCH_EXT))


def is_archive_split(file):
    """
    Checks if a file is part of a split archive.
    """
    return bool(re_search(SPLIT_REGEX, file))


async def clean_target(path):
    """
    Cleans a target path by removing the file or directory.
    """
    if await aiopath.exists(path):
        LOGGER.info(f"🧹 Cleaning Target: {path}")
        try:
            if await aiopath.isdir(path):
                await aiormtree(path)
            else:
                await aioremove(path)
        except Exception as e:
            LOGGER.error(f"Failed to clean target {path}: {e}")


async def clean_download(path):
    """
    Cleans a download path by removing the directory.
    """
    if await aiopath.exists(path):
        LOGGER.info(f"🧹 Cleaning Download: {path}")
        try:
            await aiormtree(path)
        except Exception as e:
            LOGGER.error(f"Failed to clean download {path}: {e}")


async def start_cleanup():
    """
    Starts a cleanup by deleting all torrents and recreating the download directory.
    """
    get_client().torrents_delete(torrent_hashes="all")
    try:
        await aiormtree(DOWNLOAD_DIR)
    except Exception as e:
        LOGGER.error(f"Failed to clean download directory: {e}")
    await makedirs(DOWNLOAD_DIR, exist_ok=True)


def clean_all():
    """
    Cleans all downloads from aria2 and qBittorrent, and removes the download directory.
    """
    aria2.remove_all(True)
    get_client().torrents_delete(torrent_hashes="all")
    try:
        rmtree(DOWNLOAD_DIR)
    except Exception as e:
        LOGGER.error(f"Failed to remove download directory: {e}")


def exit_clean_up(signal, frame):
    """
    Cleans up and exits the bot gracefully.
    """
    try:
        LOGGER.info("⏳ Please wait, cleaning up and stopping running downloads...")
        clean_all()
        srun(['pkill', '-9', '-f', f'gunicorn|{bot_cache["pkgs"][-1]}'])
        sexit(0)
    except KeyboardInterrupt:
        LOGGER.warning("⚠️ Force exiting before cleanup finishes!")
        sexit(1)


async def clean_unwanted(path):
    """
    Cleans unwanted files and folders from a path.
    """
    LOGGER.info(f"🧹 Cleaning unwanted files/folders in: {path}")
    for dirpath, _, files in await sync_to_async(walk, path, topdown=False):
        for filee in files:
            if filee.endswith(".!qB") or (filee.endswith('.parts') and filee.startswith('.')):
                await aioremove(ospath.join(dirpath, filee))
        if dirpath.endswith((".unwanted", "splited_files_mltb", "copied_mltb")):
            await aiormtree(dirpath)
    for dirpath, _, files in await sync_to_async(walk, path, topdown=False):
        if not await listdir(dirpath):
            await rmdir(dirpath)


async def get_path_size(path):
    """
    Gets the total size of a path (file or directory).
    """
    if await aiopath.isfile(path):
        return await aiopath.getsize(path)
    total_size = 0
    for root, dirs, files in await sync_to_async(walk, path):
        for f in files:
            abs_path = ospath.join(root, f)
            total_size += await aiopath.getsize(abs_path)
    return total_size


async def count_files_and_folders(path):
    """
    Counts the number of files and folders in a path.
    """
    total_files = 0
    total_folders = 0
    for _, dirs, files in await sync_to_async(walk, path):
        total_files += len(files)
        for f in files:
            if f.endswith(tuple(GLOBAL_EXTENSION_FILTER)):
                total_files -= 1
        total_folders += len(dirs)
    return total_folders, total_files


def get_base_name(orig_path):
    """
    Gets the base name of a file without its archive extension.
    """
    extension = next(
        (ext for ext in ARCH_EXT if orig_path.lower().endswith(ext)), ''
    )
    if extension:
        return re_split(f'{extension}$', orig_path, maxsplit=1, flags=I)[0]
    raise NotSupportedExtractionArchive('File format not supported for extraction')


def get_mime_type(file_path):
    """
    Gets the mime type of a file.
    """
    mime = Magic(mime=True)
    return mime.from_file(file_path) or "text/plain"


def check_storage_threshold(size, threshold, arch=False, alloc=False):
    """
    Checks if there is enough free storage to download a file.
    """
    free = disk_usage(DOWNLOAD_DIR).free
    if not alloc:
        required = size * 2 if arch else size
        return free - required >= threshold
    if not arch:
        return free >= threshold
    return free - size >= threshold


async def join_files(path):
    """
    Joins split binary files in a directory.
    """
    files = await listdir(path)
    results = []
    for file_ in files:
        if re_search(r"\.0+2$", file_) and await sync_to_async(get_mime_type, f'{path}/{file_}') == 'application/octet-stream':
            final_name = file_.rsplit('.', 1)[0]
            cmd = f'cat {path}/{final_name}.* > {path}/{final_name}'
            _, stderr, code = await cmd_exec(cmd, True)
            if code != 0:
                LOGGER.error(f'⛔️ Failed to join {final_name}, stderr: {stderr}')
            else:
                results.append(final_name)
    if not results:
        LOGGER.warning('🤔 No binary files to join!')
        return

    LOGGER.info('✅ Join completed!')
    for res in results:
        for file_ in files:
            if re_search(fr"{res}\.0[0-9]+$", file_):
                await aioremove(f'{path}/{file_}')
