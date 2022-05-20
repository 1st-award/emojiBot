import DiscordEmbed
import discord
import random
from discord.ext import commands


async def join_channel(message: discord.Message):
    voicechannel = message.author.voice.channel
    try:
        await voicechannel.connect(reconnect=True)
    except:
        pass


class Select(commands.Cog, name="선택"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="선택", help="선택 장애가 있는 당신에게 유용한 기능입니다", usage='`!선택`\t`선택1`\t`선택2`...')
    async def select(self, ctx):
        await ctx.message.delete()
        args = ctx.message.content[4:].strip()
        args = args.replace(" vs ", " ")
        args = args.replace(" VS ", " ")
        args = list(map(str, args.split()))
        result = random.choice(args)
        command = ""
        for arg in args:
            command += arg + " VS "
        command = command[:-3]
        user_name = ctx.message.author.nick
        if user_name is None:
            user_name = ctx.message.author.name
        discord_embed = DiscordEmbed.info(command, result)
        discord_embed.set_author(name=user_name, icon_url=ctx.message.author.avatar_url)
        await ctx.send(embed=discord_embed)

    @select.error
    async def select_error(self, ctx, error: commands.errors.CommandInvokeError, discord_embed=None):
        if isinstance(error, discord.ext.commands.errors.MissingRequiredArgument):
            discord_embed = DiscordEmbed.warning("선택지 부족", "선택지가 부족합니다.")
        await ctx.send(embed=discord_embed, delete_after=10.0)

    @commands.command(name="띨", help="에펙 예상 등수 추첨기", usage="`!띨`")
    async def random_number(self, ctx):
        await ctx.message.delete()
        number_dic = {"0": ":zero:", "1": ":one:", "2": ":two:", "3": ":three:", "4": ":four:", "5": ":five:",
                      "6": ":six:", "7": ":seven:", "8": ":eight:", "9": ":nine:"}
        result_number = str(random.randrange(1, 21))
        predict_rank = ""
        for number in result_number:
            predict_rank += number_dic[number]
        discord_embed = DiscordEmbed.info("예상 등수", predict_rank)
        await ctx.send(embed=discord_embed)

    @random_number.error
    async def random_number_error(self, ctx, error: commands.errors.CommandInvokeError, discord_embed=None):
        discord_embed = DiscordEmbed.warning("알 수 없는 오류", error)
        await ctx.send(embed=discord_embed)


def setup(bot):
    bot.add_cog(Select(bot))
