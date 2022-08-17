import asyncio
import random

from discord import app_commands, Message, Interaction
from discord.ext import commands
from Util import DiscordEmbed, DiscordUI


async def join_channel(message: Message):
    voice_channel = message.author.voice.channel
    try:
        await voice_channel.connect(reconnect=True)
    except:
        pass


class Select(commands.Cog, name="선택"):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="선택", description="선택 장애가 있는 당신에게 유용한 기능입니다")
    @app_commands.describe(select="2개 이상 입력해주세요")
    @app_commands.rename(select="입력해주세요")
    async def select(self, interaction: Interaction, select: str):
        args = select.strip()
        args = args.replace(" vs ", " ")
        args = args.replace(" VS ", " ")
        args = list(map(str, args.split()))
        result = random.choice(args)
        command = ""
        for arg in args:
            command += arg + " VS "
        command = command[:-3]
        user_name = interaction.user.nick
        if user_name is None:
            user_name = interaction.user.name
        discord_embed = DiscordEmbed.info(command, result)
        discord_embed.set_author(name=user_name, icon_url=interaction.user.avatar.url)
        await interaction.response.send_message(embed=discord_embed)

    @select.error
    async def select_error(self, interaction: Interaction,
                           error: commands.errors.CommandInvokeError,
                           discord_embed=None):
        if isinstance(error, commands.errors.MissingRequiredArgument):
            discord_embed = DiscordEmbed.warning("선택지 부족", "선택지가 부족합니다.")
        await interaction.response.send_message(embed=discord_embed)
        await asyncio.sleep(10)
        await interaction.delete_original_message()

    @app_commands.command(name="띨", description="에펙 예상 등수 추첨기")
    async def random_number(self, interaction: Interaction):
        number_dic = {"0": ":zero:", "1": ":one:", "2": ":two:", "3": ":three:", "4": ":four:", "5": ":five:",
                      "6": ":six:", "7": ":seven:", "8": ":eight:", "9": ":nine:"}
        result_number = str(random.randrange(1, 21))
        predict_rank = ""
        for number in result_number:
            predict_rank += number_dic[number]
        discord_embed = DiscordEmbed.info("예상 등수", predict_rank)
        await interaction.response.send_message(embed=discord_embed)

    @random_number.error
    async def random_number_error(self, interaction: Interaction,
                                  error: commands.errors.CommandInvokeError,
                                  discord_embed=None
                                  ):
        discord_embed = DiscordEmbed.warning("알 수 없는 오류", error)
        await interaction.response.send_message(embed=discord_embed)

    @app_commands.command(name="대댄찌", description="랜덤으로 두 팀을 나눕니다.")
    async def up_side_down(self, interaction: Interaction):
        embed = DiscordEmbed.info("대댄찌", "`참가`버튼을 눌러 팀 나누기에 참여하세요!\n`종료`버튼을 눌러 결과를 확인하세요!")
        await interaction.response.send_message(embed=embed, view=DiscordUI.InviteButton(embed))


async def setup(bot):
    await bot.add_cog(Select(bot))
