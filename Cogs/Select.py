import DiscordEmbed
import discord
import random
from discord.ext import commands


class Select(commands.Cog, name="선택"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="선택", help="선택 장애가 있는 당신에게 유용한 기능입니다", usage='`!선택\t`선택`\t`선택2')
    async def select(self, ctx):
        await ctx.message.delete()
        args = ctx.message.content[4:].strip()
        result = random.choice(list(map(str, args.split())))
        discord_embed = DiscordEmbed.info("선택 결과", result)
        await ctx.send(embed=discord_embed, delete_after=60.0)

    @select.error
    async def select_error(self, ctx, error: commands.errors.CommandInvokeError, discord_embed=None):
        if isinstance(error, discord.ext.commands.errors.MissingRequiredArgument):
            discord_embed = DiscordEmbed.warning("선택지 부족", "선택지가 부족합니다.")
        await ctx.send(embed=discord_embed, delete_after=10.0)


def setup(bot):
    bot.add_cog(Select(bot))
