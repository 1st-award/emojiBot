import asyncio
import random
import logging
import discord

logger = logging.getLogger(__name__)

from discord import app_commands, Message, Interaction
from discord.ext import commands
from Util import DiscordEmbed, DiscordUI


async def join_channel(message: Message):
    voice = getattr(message.author, "voice", None)
    if voice is None:
        return
    voice_channel = voice.channel
    try:
        await voice_channel.connect(reconnect=True)
    except (discord.ClientException, discord.HTTPException):
        logger.exception("Voice connection failed: guild_id=%s", message.guild.id)


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
        args = args.split()
        if len(args) < 2:
            raise ValueError("선택지를 두 개 이상 입력해주세요.")
        result = random.choice(args)
        command = " VS ".join(args)
        user_name = interaction.user.display_name
        discord_embed = DiscordEmbed.info(command, result)
        discord_embed.set_author(name=user_name, icon_url=interaction.user.display_avatar.url)
        await interaction.response.send_message(embed=discord_embed)

    @select.error
    async def select_error(self, interaction: Interaction,
                           error: commands.errors.CommandInvokeError,
                           discord_embed=None):
        await self.bot.tree.on_error(interaction, error)

    @app_commands.command(name="띨", description="에펙 예상 등수 추첨기")
    async def random_number(self, interaction: Interaction):
        number_dic = {"0": ":zero:", "1": ":one:", "2": ":two:", "3": ":three:", "4": ":four:", "5": ":five:",
                      "6": ":six:", "7": ":seven:", "8": ":eight:", "9": ":nine:"}
        result_number = str(random.randrange(1, 21))
        predict_rank = "".join(number_dic[number] for number in result_number)
        discord_embed = DiscordEmbed.info("예상 등수", predict_rank)
        await interaction.response.send_message(embed=discord_embed)

    @random_number.error
    async def random_number_error(self, interaction: Interaction,
                                  error: commands.errors.CommandInvokeError,
                                  discord_embed=None
                                  ):
        await self.bot.tree.on_error(interaction, error)

    @app_commands.command(name="대댄찌", description="랜덤으로 두 팀을 나눕니다.")
    async def up_side_down(self, interaction: Interaction):
        embed = DiscordEmbed.info("대댄찌", "`참가`버튼을 눌러 팀 나누기에 참여하세요!\n`종료`버튼을 눌러 결과를 확인하세요!")
        await interaction.response.send_message(embed=embed, view=DiscordUI.InviteButton(embed))


async def setup(bot):
    await bot.add_cog(Select(bot))
