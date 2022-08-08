import discord
from discord.app_commands import AppCommandError
from discord.ext import commands
from Util import DiscordEmbed, DiscordUI


class Errorhandler(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # setting the handler
        bot.tree.on_error = self.on_app_command_error

    # the global error handler
    async def on_app_command_error(self, interaction: discord.Interaction, error: AppCommandError):
        print(error)
        embed = DiscordEmbed.warning("알 수 없는 애러", error)
        await interaction.response.send_message(embed=embed, view=DiscordUI.ReportButton(self.bot, error), ephemeral=True)


async def setup(bot):
    await bot.add_cog(Errorhandler(bot))
