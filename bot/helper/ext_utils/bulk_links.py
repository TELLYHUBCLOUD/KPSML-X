#!/usr/bin/env python3
from aiofiles import open as aiopen
from aiofiles.os import remove as aioremove


async def get_links_from_message(text, bulk_start, bulk_end):
    """
    Extracts links from a message text, supporting bulk selection.
    """
    links_list = [item.strip() for item in text.split('\n') if item]

    if bulk_start and bulk_end:
        return links_list[bulk_start:bulk_end]
    if bulk_start:
        return links_list[bulk_start:]
    if bulk_end:
        return links_list[:bulk_end]

    return links_list


async def get_links_from_file(message, bulk_start, bulk_end):
    """
    Extracts links from a text file, supporting bulk selection.
    """
    try:
        text_file_dir = await message.download()
        async with aiopen(text_file_dir, 'r+') as f:
            lines = await f.readlines()

        links_list = [line.strip() for line in lines if line]

        if bulk_start and bulk_end:
            return links_list[bulk_start:bulk_end]
        if bulk_start:
            return links_list[bulk_start:]
        if bulk_end:
            return links_list[:bulk_end]

        return links_list
    finally:
        if text_file_dir:
            await aioremove(text_file_dir)


async def extract_bulk_links(message, bulk_start, bulk_end):
    """
    Main function to extract bulk links from either a message or a file.
    """
    bulk_start = int(bulk_start) if bulk_start else 0
    bulk_end = int(bulk_end) if bulk_end else 0

    reply_to = message.reply_to_message
    if not reply_to:
        return []

    if (file_ := reply_to.document) and file_.mime_type == 'text/plain':
        return await get_links_from_file(reply_to, bulk_start, bulk_end)

    if text := reply_to.text:
        return await get_links_from_message(text, bulk_start, bulk_end)

    return []
