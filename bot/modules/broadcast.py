#!/usr/bin/env python3
from time import time
from uuid import uuid4
from asyncio import sleep
from pyrogram.handlers import MessageHandler
from pyrogram.filters import command
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated

from bot import bot, LOGGER, DATABASE_URL
from bot.helper.ext_utils.db_handler import DbManger
from bot.helper.telegram_helper.message_utils import sendMessage, editMessage
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.ext_utils.bot_utils import new_task, get_readable_time

broadcast_cache = {}

@new_task
async def broadcast(_, message):
    """
    Broadcasts a message to all users in the database.
    """
    if not DATABASE_URL:
        await sendMessage(message, 'DATABASE_URL is not provided!')
        return

    reply = message.reply_to_message
    args = message.command

    bc_id, is_forward, is_quiet, is_delete, is_edit = '', False, False, False, False

    if len(args) > 1:
        if not args[1].startswith('-'):
            bc_id = args[1] if broadcast_cache.get(args[1]) else ''
            if not bc_id:
                await sendMessage(message, "Broadcast ID not found. Cannot edit or delete after a restart.")
                return

        for arg in args:
            if arg in ['-f', '-forward'] and reply: is_forward = True
            if arg in ['-q', '-quiet'] and reply: is_quiet = True
            if arg in ['-d', '-delete'] and bc_id: is_delete = True
            if arg in ['-e', '-edit'] and bc_id and reply: is_edit = True

    if not bc_id and not reply:
        await sendMessage(message, '<b>Broadcast Help:</b>\n\n'
                                   '<b>Reply to a message to broadcast:</b>\n'
                                   '<code>/broadcast [-f] [-q]</code>\n\n'
                                   '<code>-f</code>: Forward the message.\n'
                                   '<code>-q</code>: Send quietly.\n\n'
                                   '<b>Edit a broadcast:</b>\n'
                                   '<code>/broadcast [broadcast_id] -e</code>\n\n'
                                   '<b>Delete a broadcast:</b>\n'
                                   '<code>/broadcast [broadcast_id] -d</code>')
        return

    total, success, blocked, deleted, unsuccessful = 0, 0, 0, 0, 0

    if is_delete:
        status_msg = await sendMessage(message, 'Deleting broadcast messages...')
        for msg in (msgs := broadcast_cache.get(bc_id, [])):
            try:
                await msg.delete()
                await sleep(0.5)
                msgs.remove(msg)
                success += 1
            except Exception:
                unsuccessful += 1
            total += 1
        await editMessage(status_msg, f'<b>Broadcast Deleted!</b>\n\n'
                                      f'<b>Total:</b> {total}\n'
                                      f'<b>Success:</b> {success}\n'
                                      f'<b>Failed:</b> {unsuccessful}\n\n'
                                      f'<b>Broadcast ID:</b> <code>{bc_id}</code>')
        return

    if is_edit:
        status_msg = await sendMessage(message, 'Editing broadcast messages...')
        for msg in broadcast_cache.get(bc_id, []):
            if hasattr(msg, "forward_from"):
                await editMessage(status_msg, "Forwarded messages cannot be edited.")
                return
            try:
                await msg.edit(text=reply.text, entities=reply.entities, reply_markup=reply.reply_markup)
                await sleep(0.5)
                success += 1
            except FloodWait as e:
                await sleep(e.value)
                await msg.edit(text=reply.text, entities=reply.entities, reply_markup=reply.reply_markup)
                success += 1
            except Exception:
                unsuccessful += 1
            total += 1
        await editMessage(status_msg, f'<b>Broadcast Edited!</b>\n\n'
                                      f'<b>Total:</b> {total}\n'
                                      f'<b>Success:</b> {success}\n'
                                      f'<b>Failed:</b> {unsuccessful}\n\n'
                                      f'<b>Broadcast ID:</b> <code>{bc_id}</code>')
        return

    start_time = time()
    status_format = ('<b>Broadcast Stats:</b>\n\n'
                     '<b>Total:</b> {total}\n'
                     '<b>Success:</b> {success}\n'
                     '<b>Blocked:</b> {blocked}\n'
                     '<b>Deleted:</b> {deleted}\n'
                     '<b>Failed:</b> {unsuccessful}')

    status_msg = await sendMessage(message, status_format.format(**locals()))

    bc_hash = str(uuid4())
    broadcast_cache[bc_hash] = []

    for uid in (await DbManger().get_pm_uids()):
        bc_msg = None
        try:
            bc_msg = await (reply.forward if is_forward else reply.copy)(uid, disable_notification=is_quiet)
            success += 1
        except FloodWait as e:
            await sleep(e.value)
            bc_msg = await (reply.forward if is_forward else reply.copy)(uid, disable_notification=is_quiet)
            success += 1
        except UserIsBlocked:
            await DbManger().rm_pm_user(uid)
            blocked += 1
        except InputUserDeactivated:
            await DbManger().rm_pm_user(uid)
            deleted += 1
        except Exception:
            unsuccessful += 1

        if bc_msg:
            broadcast_cache[bc_hash].append(bc_msg)
        total += 1

        if (time() - start_time) % 10 < 1:
            await editMessage(status_msg, status_format.format(**locals()))

    await editMessage(status_msg, f"{status_format.format(**locals())}\n\n"
                                  f"<b>Elapsed Time:</b> {get_readable_time(time() - start_time)}\n"
                                  f"<b>Broadcast ID:</b> <code>{bc_hash}</code>")


bot.add_handler(MessageHandler(broadcast, filters=command(BotCommands.BroadcastCommand) & CustomFilters.sudo))
