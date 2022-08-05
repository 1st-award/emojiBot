import asyncio
import discord.ui
from discord.ext import commands
from Util import DiscordEmbed


class LinkButton(discord.ui.View):
    def __init__(self, label: str, url: str):
        super().__init__()
        self.add_item(discord.ui.Button(label=label, url=url))


class ReportButton(discord.ui.View):
    def __init__(self, bot: commands.Bot, error: discord.app_commands.AppCommandError):
        super().__init__()
        self.bot = bot
        self.error = error

    @discord.ui.button(label="제작자 일 시키기", style=discord.ButtonStyle.danger)
    async def report(self, interaction: discord.Interaction, button: discord.ui.Button):
        bot_owner = self.bot.get_user(276532581829181441)
        embed = DiscordEmbed.warning("애러발생 일해라 ㅠ", self.error.__traceback__)
        await bot_owner.send(embed=embed)
        button.label = "전송완료"
        button.disabled = True

        await interaction.response.edit_message(view=self)
        await asyncio.sleep(5)
        await interaction.delete_original_message()
