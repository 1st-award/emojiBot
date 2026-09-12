import asyncio
import logging
logger = logging.getLogger(__name__)

from Util import DiscordEmbed, ImojiUtil, SQLUtil, DiscordUI
from discord import app_commands, Interaction, Attachment
from discord.ext import commands


@app_commands.guild_only()
class Emoji(commands.Cog, name="기본 명령어"):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="등록", description="이모지 등록 명령어")
    @app_commands.describe(emoji_command="콤마(,)단위로 명령어를 여러개 넣을 수 있습니다.",
                           attachment="지원 파일: jpg, png, gif, GIF 조건: 크기(3MB이하) 해상도(128X128이상)")
    @app_commands.rename(emoji_command="명령어", attachment="이모지")
    async def emoji_register(self, interaction: Interaction, emoji_command: str,
                             attachment: Attachment):
        file_name = ImojiUtil.attachment_filename(attachment)
        await interaction.response.defer()
        SQLUtil.register_emoji(file_name, emoji_command, interaction.guild_id)
        try:
            await ImojiUtil.save_emoji(attachment, interaction.guild_id)
        except Exception:
            SQLUtil.emoji_remove(emoji_command, interaction.guild_id)
            ImojiUtil.emoji_remove(file_name, interaction.guild_id)
            raise
        discord_embed = DiscordEmbed.info("등록 완료", f"{emoji_command}이(가) 등록되었습니다.")
        await interaction.followup.send(embed=discord_embed)
        await asyncio.sleep(60)
        await interaction.delete_original_response()

    @emoji_register.error
    async def emoji_register_error(self, interaction: Interaction, error: commands.errors.CommandInvokeError,
                                   discord_embed=None):
        await self.bot.tree.on_error(interaction, error)

    @app_commands.command(name="삭제", description="이모지 삭제 명령어")
    @app_commands.describe(emoji_command="이모지 명령어를 넣어주세요!")
    @app_commands.rename(emoji_command="명령어")
    async def emoji_remove(self, interaction: Interaction, emoji_command: str):
        search_result_arg = SQLUtil.emoji_search_exact(emoji_command, interaction.guild_id)
        if isinstance(search_result_arg, tuple):
            SQLUtil.emoji_remove(emoji_command, interaction.guild_id)
            ImojiUtil.emoji_remove(search_result_arg[0], interaction.guild_id)
            discord_embed = DiscordEmbed.info("삭제 완료", f"{emoji_command}이(가) 삭제되었습니다.")
            await interaction.response.send_message(embed=discord_embed)
            await asyncio.sleep(10)
            await interaction.delete_original_response()
        else:
            raise FileNotFoundError(f"`{emoji_command}`는(은) 명령어로 등록되어있지 않습니다.")

    @emoji_remove.error
    async def emoji_remove_error(self, interaction: Interaction, error: commands.errors.CommandInvokeError):
        await self.bot.tree.on_error(interaction, error)

    @app_commands.command(name="글자", description="글자티콘을 생성합니다")
    @app_commands.rename(comment="글", background_color="배경색상")
    @app_commands.choices(background_color=[
        app_commands.Choice(name="파랑", value="#3b4890"),
        app_commands.Choice(name="보라", value="#b4b4e1"),
        app_commands.Choice(name="분홍", value="#f5e1f0"),
        app_commands.Choice(name="초록", value="#d2f0e6"),
        app_commands.Choice(name="흰색", value="#ffffff"),
        app_commands.Choice(name="검정", value="#333333"),
    ])
    async def emoji_comment(self, interaction: Interaction, comment: str, background_color: app_commands.Choice[str] | None = None):
        if background_color is None:
            background_color = app_commands.Choice(name="파랑", value="#3b4890")
        image = ImojiUtil.create_image(comment, background_color.value)
        embed, file = DiscordEmbed.bytesIO_image(interaction.user, image)
        await interaction.response.send_message(embed=embed, file=file)

    @app_commands.command(name="리스트", description="등록된 이모지 리스트")
    async def emoji_list(self, interaction: Interaction):
        search_result = SQLUtil.emoji_search_all(interaction.guild_id)
        discord_embed = await DiscordEmbed.emoji_list(search_result)
        await interaction.response.send_message(embed=discord_embed)
        await asyncio.sleep(300)
        await interaction.delete_original_response()

    @emoji_list.error
    async def emoji_list_error(self, interaction: Interaction, error: commands.errors.CommandInvokeError):
        await self.bot.tree.on_error(interaction, error)

    @app_commands.command(name="디시콘", description="펀가놈의 디시콘을 사용할 수 있습니다.")
    async def funz_list(self, interaction: Interaction):
        discord_embed = DiscordEmbed.info("펀 가 이 동", "디시콘 명령어 리스트\n`~`\t`디시콘 명령어`로 사용할 수 있습니다")
        await interaction.response.send_message(embed=discord_embed,
                                                view=DiscordUI.LinkButton("펀 가 이 동", "https://funzinnu.com/dccon.html")
                                                )
        await asyncio.sleep(300)
        await interaction.delete_original_response()

    @app_commands.command(name="랜덤", description="이모지 중 무작위 하나를 보여줍니다. ~랜덤을 이용해주세요")
    async def random_emoji(self, interaction: Interaction):
        discord_embed = DiscordEmbed.warning("`~랜덤`을 사용해주세요.", "")
        await interaction.response.send_message(embed=discord_embed)
        await asyncio.sleep(10)
        await interaction.delete_original_response()

    @app_commands.command(name="복사", description="이모지 리스트 복사")
    @app_commands.checks.has_permissions(administrator=True)
    async def copy_imoji(self, interaction: Interaction, to_guild_id: int, from_guild_id: int):
        if not await self.bot.is_owner(interaction.user):
            raise app_commands.CheckFailure("서버 간 복사는 봇 소유자만 실행할 수 있습니다.")
        if to_guild_id == from_guild_id or min(to_guild_id, from_guild_id) <= 0:
            raise ValueError("서로 다른 서버 ID를 입력해주세요.")
        rows = [(from_guild_id, path, command) for _, path, command in SQLUtil.emoji_search_all(to_guild_id)]
        await interaction.response.defer()
        await asyncio.to_thread(ImojiUtil.emoji_dir_copy, to_guild_id, from_guild_id)
        SQLUtil.insert_guild(from_guild_id)
        SQLUtil.replace_emoji(from_guild_id, rows)
        discord_embed = DiscordEmbed.info("복사 완료")
        await interaction.followup.send(embed=discord_embed)
        await asyncio.sleep(10)
        await interaction.delete_original_response()

    @copy_imoji.error
    async def copy_imoji_error(self, interaction: Interaction, error: commands.errors.CommandInvokeError):
        await self.bot.tree.on_error(interaction, error)

    def switch_guild(self, imoji: tuple, guild: int):
        list_imoji = list(imoji)
        list_imoji[0] = guild
        return tuple(list_imoji)


async def setup(bot):
    await bot.add_cog(Emoji(bot))
