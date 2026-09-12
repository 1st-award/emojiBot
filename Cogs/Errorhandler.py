import logging
from discord import Interaction
from discord.app_commands import AppCommandError, CheckFailure
from discord.ext import commands
from Util import DiscordEmbed

logger = logging.getLogger(__name__)


class Errorhandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.previous_handler = bot.tree.on_error
        bot.tree.on_error = self.on_app_command_error

    def cog_unload(self):
        self.bot.tree.on_error = self.previous_handler

    async def on_app_command_error(self, interaction: Interaction, error: AppCommandError):
        if interaction.extras.get("error_handled"):
            return
        interaction.extras["error_handled"] = True
        original = getattr(error, "original", error)
        expected = isinstance(original, (FileNotFoundError, FileExistsError, ValueError, NotImplementedError, PermissionError, CheckFailure))
        if expected:
            logger.warning("Command rejected: guild_id=%s type=%s", interaction.guild_id, type(original).__name__)
        else:
            logger.error("Command failed: guild_id=%s", interaction.guild_id,
                         exc_info=(type(original), original, original.__traceback__))
        embed = DiscordEmbed.warning("명령어 실행 실패", "입력값, 등록 상태와 권한을 확인해주세요." if expected
                                     else "처리 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.")
        send = interaction.followup.send if interaction.response.is_done() else interaction.response.send_message
        await send(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(Errorhandler(bot))
