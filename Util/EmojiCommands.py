"""Dispatch and send tilde emoji commands independently of bot startup."""
import asyncio
import logging
import sqlite3
import discord
from Util import DiscordEmbed, SQLUtil

logger = logging.getLogger(__name__)


def resolve_emoji(command, guild_id):
    if command == "랜덤":
        result = SQLUtil.random_emoji(guild_id)
        return (result[0], result[1] == SQLUtil.GLOBAL_GUILD_ID) if result else None
    local = SQLUtil.emoji_search(command, guild_id)
    if local:
        return local[0], False
    shared = SQLUtil.emoji_global_emoji_search(command)
    return (shared[0], True) if shared else None


async def handle_emoji_message(message):
    command = message.content[1:].strip()
    if not command:
        return
    try:
        try:
            await message.delete()
        except discord.NotFound:
            pass
        except discord.Forbidden:
            logger.warning("Cannot delete command message: guild_id=%s", message.guild.id)
        result = await asyncio.to_thread(resolve_emoji, command, message.guild.id)
        if result is None:
            logger.debug("Emoji not found: guild_id=%s", message.guild.id)
            await message.channel.send(embed=DiscordEmbed.warning(
                "이모지 없음", "일치하는 이모지가 없습니다."),
                reference=message.reference, delete_after=10)
            return
        embed, image = await DiscordEmbed.picture(message, *result)
        try:
            await message.channel.send(embed=embed, file=image, reference=message.reference)
        finally:
            image.close()
    except (discord.HTTPException, OSError, sqlite3.Error, ValueError):
        logger.exception("Emoji command failed: guild_id=%s", message.guild.id)
