import asyncio
import functools

import discord

from Util import DiscordEmbed, ImojiUtil, SQLUtil, DiscordUI
from discord import app_commands
from discord.ext import commands


class Emoji(commands.Cog, name="기본 명령어"):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="등록", description="이모지 등록 명령어")
    @app_commands.describe(emoji_command="콤마(,)단위로 명령어를 여러개 넣을 수 있습니다.",
                           attachment="지원 파일: jpg, png, gif, GIF 조건: 크기(3MB이하) 해상도(128X128이상)")
    @app_commands.rename(emoji_command="명령어", attachment="이모지")
    async def emoji_register(self, interaction: discord.Interaction, emoji_command: str,
                             attachment: discord.Attachment):
        file_type = attachment.content_type.split("/")
        file_name = str(attachment.id) + "." + file_type[1]

        ImojiUtil.is_support_format(file_name)
        SQLUtil.register_emoji(file_name, emoji_command, interaction.guild_id)
        await ImojiUtil.save_emoji(attachment, interaction.guild_id)
        discord_embed = DiscordEmbed.info("등록 완료", f"{emoji_command}이(가) 등록되었습니다.")
        await interaction.response.send_message(embed=discord_embed)
        await asyncio.sleep(60)
        await interaction.delete_original_message()

    @emoji_register.error
    async def emoji_register_error(self, interaction: discord.Interaction, error: commands.errors.CommandInvokeError,
                                   discord_embed=None):
        if isinstance(error.original, IndexError):
            discord_embed = DiscordEmbed.warning("사진 없음", "등록해야 할 사진이 없습니다.")
        elif isinstance(error.original, NotImplementedError):
            discord_embed = DiscordEmbed.warning("지원하지 않는 파일", error.original)
        elif isinstance(error.original, FileExistsError):
            discord_embed = DiscordEmbed.warning("중복 명령어", error.original)
        elif isinstance(error.original, ValueError):
            discord_embed = DiscordEmbed.warning("GIF 변환 실패", error.original)
            # gif 변환 실패로인한 db에서의 명령어와 gif 삭제
            emoji_command = interaction.message.content.split()
            SQLUtil.emoji_remove(emoji_command[-1], interaction.guild_id)
            ImojiUtil.emoji_remove(interaction.message.attachments[0].filename, interaction.guild_id)
        await interaction.response.send_message(embed=discord_embed)
        await asyncio.sleep(10)
        await interaction.delete_original_message()

    @app_commands.command(name="삭제", description="이모지 삭제 명령어")
    @app_commands.describe(emoji_command="이모지 명령어를 넣어주세요!")
    @app_commands.rename(emoji_command="명령어")
    async def emoji_remove(self, interaction: discord.Interaction, emoji_command: str):
        search_result_arg = SQLUtil.emoji_search(emoji_command, interaction.guild_id)
        if isinstance(search_result_arg, tuple):
            SQLUtil.emoji_remove(emoji_command, interaction.guild_id)
            ImojiUtil.emoji_remove(search_result_arg[0], interaction.guild_id)
            discord_embed = DiscordEmbed.info("삭제 완료", f"{emoji_command}이(가) 삭제되었습니다.")
            await interaction.response.send_message(embed=discord_embed)
            await asyncio.sleep(10)
            await interaction.delete_original_message()
        else:
            raise FileNotFoundError(f"`{emoji_command}`는(은) 명령어로 등록되어있지 않습니다.")

    @emoji_remove.error
    async def emoji_remove_error(self, interaction: discord.Interaction, error: commands.errors.CommandInvokeError):
        if isinstance(error.original, FileNotFoundError):
            discord_embed = DiscordEmbed.warning("삭제 오류", error.original)
        elif isinstance(error.original, PermissionError):
            discord_embed = DiscordEmbed.warning("삭제 실패", "현재 사용 중인 이모지이므로 잠시 후 다시 시도해 주세요.")
        await interaction.response.send_message(embed=discord_embed)
        await asyncio.sleep(10)
        await interaction.delete_original_message()

    @app_commands.command(name="리스트", description="등록된 이모지 리스트")
    async def emoji_list(self, interaction: discord.Interaction):
        search_result = SQLUtil.emoji_search_all(interaction.guild_id)
        print(type(search_result), search_result)
        discord_embed = await DiscordEmbed.emoji_list(search_result)
        await interaction.response.send_message(embed=discord_embed)
        await asyncio.sleep(300)
        await interaction.delete_original_message()

    @emoji_list.error
    async def emoji_list_error(self, interaction: discord.Interaction, error: commands.errors.CommandInvokeError):
        if isinstance(error.original, FileNotFoundError):
            discord_embed = DiscordEmbed.warning("이모지 없음", error.original)
        await interaction.response.send_message(embed=discord_embed)
        await asyncio.sleep(30)
        await interaction.delete_original_message()

    @app_commands.command(name="디시콘", description="펀가놈의 디시콘을 사용할 수 있습니다.")
    async def funz_list(self, interaction: discord.Interaction):
        discord_embed = DiscordEmbed.info("펀 가 이 동", "디시콘 명령어 리스트\n`~`\t`디시콘 명령어`로 사용할 수 있습니다")
        await interaction.response.send_message(embed=discord_embed,
                                                view=DiscordUI.LinkButton("펀 가 이 동", "https://funzinnu.com/dccon.html")
                                                )
        await asyncio.sleep(300)
        await interaction.delete_original_message()

    @app_commands.command(name="랜덤", description="이모지 중 무작위 하나를 보여줍니다. ~랜덤을 이용해주세요")
    async def random_emoji(self, interaction: discord.Interaction):
        discord_embed = DiscordEmbed.warning("`~랜덤`을 사용해주세요.", "")
        await interaction.response.send_message(embed=discord_embed)
        await asyncio.sleep(10)
        await interaction.delete_original_message()

    @app_commands.command(name="복사", description="이모지 리스트 복사")
    @app_commands.checks.has_permissions(administrator=True)
    async def copy_imoji(self, interaction: discord.Interaction, to_guild_id: int, from_guild_id: int):
        SQLUtil.remove_guild(from_guild_id)
        SQLUtil.insert_guild(from_guild_id)
        imoji_args = SQLUtil.emoji_search_all(to_guild_id)
        imoji_args = list(map(functools.partial(self.switch_guild, guild=from_guild_id), imoji_args))
        SQLUtil.emoji_insert_all(from_guild_id, imoji_args)
        ImojiUtil.emoji_dir_copy(to_guild_id, from_guild_id)
        discord_embed = DiscordEmbed.info("복사 완료")
        await interaction.response.send_message(embed=discord_embed)
        await asyncio.sleep(10)
        await interaction.delete_original_message()

    @copy_imoji.error
    async def copy_imoji_error(self, interaction: discord.Interaction, error: commands.errors.CommandInvokeError):
        discord_embed = DiscordEmbed.warning("머지 애러 발생", error.__traceback__)
        await interaction.response.send_message(embed=discord_embed)
        await asyncio.sleep(10)
        await interaction.delete_original_message()

    def switch_guild(self, imoji: tuple, guild: int):
        list_imoji = list(imoji)
        list_imoji[0] = guild
        return tuple(list_imoji)


async def setup(bot):
    await bot.add_cog(Emoji(bot))
