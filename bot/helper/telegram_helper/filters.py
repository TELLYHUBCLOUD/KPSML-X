#!/usr/bin/env python3
from pyrogram.filters import create
from pyrogram.enums import ChatType

from bot import user_data, OWNER_ID
from bot.helper.telegram_helper.message_utils import chat_info


class CustomFilters:
    """
    Custom filters for Pyrogram.
    """

    @staticmethod
    async def owner_filter(self, _, message):
        """
        Filter for messages from the bot owner.
        """
        user = message.from_user or message.sender_chat
        return user and user.id == OWNER_ID

    owner = create(owner_filter)

    @staticmethod
    async def authorized_user(self, _, message):
        """
        Filter for authorized users and chats.
        """
        user = message.from_user or message.sender_chat
        if not user: return False

        uid = user.id
        if uid == OWNER_ID or (uid in user_data and (user_data[uid].get('is_auth') or user_data[uid].get('is_sudo'))):
            return True

        chat_id = message.chat.id
        if chat_id in user_data and user_data[chat_id].get('is_auth'):
            if not (topic_ids := user_data[chat_id].get('topic_ids')):
                return True
            if (is_forum := message.reply_to_message) and ((not is_forum.text and not is_forum.caption and is_forum.id in topic_ids) or
                                                           ((is_forum.text or is_forum.caption) and
                                                           ((not is_forum.reply_to_top_message_id and is_forum.reply_to_message_id in topic_ids) or
                                                           (is_forum.reply_to_top_message_id in topic_ids)))):
                return True

        return False

    authorized = create(authorized_user)

    @staticmethod
    async def authorized_usetting(self, _, message):
        """
        Filter for authorized users in user settings.
        """
        user = message.from_user or message.sender_chat
        if not user: return False

        uid = user.id
        chat_id = message.chat.id
        
        if uid == OWNER_ID or (uid in user_data and (user_data[uid].get('is_auth') or user_data[uid].get('is_sudo'))) or \
           (chat_id in user_data and user_data[chat_id].get('is_auth')):
            return True

        if message.chat.type == ChatType.PRIVATE:
            for channel_id in user_data:
                if user_data[channel_id].get('is_auth') and str(channel_id).startswith('-100'):
                    try:
                        if await (await chat_info(channel_id)).get_member(uid):
                            return True
                    except:
                        pass
        return False

    authorized_uset = create(authorized_usetting)

    @staticmethod
    async def sudo_user(self, _, message):
        """
        Filter for sudo users.
        """
        user = message.from_user or message.sender_chat
        return user and (user.id == OWNER_ID or (user.id in user_data and user_data[user.id].get('is_sudo')))

    sudo = create(sudo_user)
    
    @staticmethod
    async def blacklist_user(self, _, message):
        """
        Filter for blacklisted users.
        """
        user = message.from_user or message.sender_chat
        return user and user.id != OWNER_ID and user.id in user_data and user_data[user.id].get('is_blacklist')

    blacklisted = create(blacklist_user)
