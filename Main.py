import asyncio
import os
import random

import discord
from discord import app_commands, Interaction, Object, Intents, Guild, Message, Embed, Colour
from discord.ext import commands
from dotenv import load_dotenv
from Util import DiscordEmbed, ImojiUtil, SQLUtil, DiscordUI

# 봇 권한 부여
MY_GUILD = Object(id=349181108669382657)


class Bot(commands.Bot):
    def __init__(self, *, intents: Intents):
        super().__init__(command_prefix='.', intents=intents)

    async def setup_hook(self):
        # Cogs Load
        for filename in os.listdir("Cogs"):
            if filename.endswith(".py"):
                await self.load_extension(f"Cogs.{filename[:-3]}")
        # This copies the global commands over to your guild.
        # A common practice for syncing is to pick a specific guild for testing
        # self.tree.copy_global_to(guild=MY_GUILD)
        # await self.tree.sync(guild=MY_GUILD)

        # When you're done testing
        self.tree.clear_commands(guild=MY_GUILD)
        await self.tree.sync(guild=MY_GUILD)

        # When you're ready to publish your commands
        await self.tree.sync()


intents = Intents.all()
bot = Bot(intents=intents)
# !도움말을 위한 기존에 있는 help 제거
bot.remove_command('help')
# 이미지 분석 결과 출력 스위치
image_filter_result_img_switch = False
image_remove_switch = True

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# 봇 준비
@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game(name="!도움말"))
    print(f"봇 이름: {bot.user.name}")
    for guilds in bot.guilds:
        print(str(guilds.owner_id))
    print("-" * 30)


# 봇이 길드에 들어갔을 때
@bot.event
async def on_guild_join(guild):
    ImojiUtil.emoji_dir_create(guild.id)
    SQLUtil.insert_guild(guild.id)
    for channel in guild.text_channels:
        if channel.permissions_for(guild.me).send_messages:
            discord_embed = DiscordEmbed.info(
                '봇 참가', '이모지 봇이 참여했습니다. 명령어는 `!도움말`입니다')
            await channel.send(embed=discord_embed, delete_after=10.0)
        break


# 봇이 길드에서 삭제될 때
@bot.event
async def on_guild_remove(guild: Guild):
    print("remove data before quit...")
    ImojiUtil.emoji_dir_remove(guild.id)
    SQLUtil.remove_guild(guild.id)
    print("remove success")


@bot.event
async def on_message(message: Message):
    whitelist_bot_id = [1148832483912208467, 1148832491906535474, 1148832517982531665,
                        1148832499494047775, 1148832505332519024, 1148832510017540190]
    if message.author.bot and message.author.id not in whitelist_bot_id:
        return

    is_global_icon = False
    if message.content.startswith("~"):
        await message.delete()

        msg = message.content.replace("~", "")
        if msg == "랜덤":
            result = SQLUtil.emoji_search_all(message.guild.id)
            global_result = SQLUtil.load_emoji_global_emoji()
            emoji_list = []
            for emoji_command in result:
                emoji_list.append(emoji_command[2])
            for emoji_command in global_result:
                emoji_list.append(emoji_command[2])
            msg = random.choice(emoji_list)

        result_args = SQLUtil.emoji_search(msg, message.guild.id)
        if result_args is None:
            result_args = SQLUtil.emoji_global_emoji_search(msg)
            is_global_icon = True

        if isinstance(result_args, tuple):
            discord_embed, image = await DiscordEmbed.picture(message, result_args[0], is_global_icon)
            await message.channel.send(embed=discord_embed, file=image, reference=message.reference)
        else:
            discord_embed = DiscordEmbed.warning(
                "이모지 없음", f"`{message.content}`는 이모지 리스트에 없습니다.")
            await message.channel.send(embed=discord_embed, reference=message.reference, delete_after=10.0)
    # 기존에 작성한 명령어로 이동
    await bot.process_commands(message)


@bot.tree.command(name="도움말", description="명령어를 출력, 검색합니다")
@app_commands.rename(command="명령어")
async def help_command(interaction: Interaction, command: str = None):
    embed = Embed(title="이모지 봇 도움말",
                  description="접두사는 `!` 입니다. 자세한 내용은 `!도움말`\0`명령어`를 입력하시면 됩니다.",
                  color=Colour.magenta())  # Embed 생성
    if command is None:
        command_list = bot.tree.get_commands()  # cog_data에서 명령어 리스트 구하기
        for command in command_list:  # cog_list에 대한 반복문
            if isinstance(command, app_commands.ContextMenu):
                continue
            embed.add_field(
                name=f"`{command.name}`", value=command.description, inline=True)  # 필드 추가
    else:  # func가 None이 아니면
        result = bot.tree.get_command(command)
        if result is not None:
            embed.add_field(name=f"`{result.name}`", value=result.description)
        else:
            embed = DiscordEmbed.warning("명령어 없음", "등록 되어있지 않은 명령어 입니다.")

    await interaction.response.send_message(embed=embed)  # 보내기
    await asyncio.sleep(300)
    await interaction.delete_original_response()


@bot.tree.context_menu(name="신고하기")
async def report_message(interaction: Interaction, message: Message):
    await interaction.response.send_modal(DiscordUI.ReportModal(bot, message))


# Cogs 파일(.py)을 로드
@bot.tree.command(name="로드")
@app_commands.checks.has_permissions(administrator=True)
async def load_commands(interaction: Interaction, extension: str):
    # 봇 오너
    bot_owner = bot.get_user(276532581829181441)
    await bot.load_extension(f"Cogs.{extension}")
    await bot_owner.send(f":white_check_mark: {extension}을(를) 로드했습니다!")
    await interaction.response.send_message("Load OK", ephemeral=True)


# Cogs 파일(.py)을 언로드
@bot.tree.command(name="언로드")
@app_commands.checks.has_permissions(administrator=True)
async def unload_commands(interaction: Interaction, extension: str):
    # 봇 오너
    bot_owner = bot.get_user(276532581829181441)
    await bot.unload_extension(f"Cogs.{extension}")
    await bot_owner.send(f":white_check_mark: {extension}을(를) 언로드했습니다!")
    await interaction.response.send_message("Unload OK", ephemeral=True)


# Cogs 파일(.py)을 리로드
@bot.tree.command(name="리로드")
@app_commands.checks.has_permissions(administrator=True)
async def reload_commands(interaction: Interaction, extension: str = None):
    # 봇 오너
    bot_owner = bot.get_user(276532581829181441)
    if extension is None:  # extension이 None이면 (그냥 !리로드 라고 썼을 때)
        for filename in os.listdir("Cogs"):
            if filename.endswith(".py"):
                await bot.unload_extension(f"Cogs.{filename[:-3]}")
                await bot.load_extension(f"Cogs.{filename[:-3]}")
        await bot_owner.send(":white_check_mark: 모든 명령어를 다시 불러왔습니다!")
    else:
        await bot.unload_extension(f"Cogs.{extension}")
        await bot.load_extension(f"Cogs.{extension}")
        await bot_owner.send(f":white_check_mark: {extension}을(를) 다시 불러왔습니다!")
    await interaction.response.send_message("Reload OK", ephemeral=True)


bot.run(BOT_TOKEN)
