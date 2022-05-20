import asyncio
import discord
import DiscordEmbed
import os
import random
import threading
import ImojiUtil
import SQLUtil
from discord.ext import commands
from Cogs import Select

# 봇 권한 부여
intents = discord.Intents(messages=True, guilds=True, members=True)
bot = commands.Bot(command_prefix='!', intents=intents)
# !도움말을 위한 기존에 있는 help 제거
bot.remove_command('help')

# Cogs Load
for filename in os.listdir("Cogs"):
    if filename.endswith(".py"):
        bot.load_extension(f"Cogs.{filename[:-3]}")


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
    SQLUtil.new_guild_join(guild.id)
    for channel in guild.text_channels:
        if channel.permissions_for(guild.me).send_messages:
            discord_embed = DiscordEmbed.info('봇 참가', '이모지 봇이 참여했습니다. 명령어는 `!도움말`입니다')
            await channel.send(embed=discord_embed, delete_after=10.0)
        break


# 봇이 길드에서 삭제될 때
@bot.event
async def on_guild_remove(guild: discord.Guild):
    print("delete all documents...")
    await ImojiUtil.emoji_dir_remove(guild.id)
    await SQLUtil.emoji_db_remove(guild.id)
    print("delete complete")


@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return    
    # 승민아조시 전용 리액션
    #if message.author.id == 332822538373562375:
    #    emoji_list = ["🇸", "🇪", "🇽", "🐧", "👍"]
    #    for emoji in emoji_list:
    #        await message.add_reaction(emoji)


    if message.content.startswith("~"):
        await message.delete()
        msg = message.content.replace("~", "")

        if msg == "랜덤":
            result = SQLUtil.emoji_search_all(message.guild.id)
            global_result = SQLUtil.load_emoji_global_emoji()
            emoji_list = []
            for emoji_command in result:
                emoji_list.append(emoji_command[1])
            for emoji_command in global_result:
                emoji_list.append(emoji_command[1])
            msg = random.choice(emoji_list)
        result_args = SQLUtil.emoji_search(msg, message.guild.id)

        if result_args is None:
            result_args = SQLUtil.emoji_global_emoji_search(msg)
        if isinstance(result_args, tuple):
            discord_embed, image = await DiscordEmbed.picture(message, result_args[0])
            if image is None:
                await message.channel.send(embed=discord_embed)
            else:
                await message.channel.send(embed=discord_embed, file=image)
        else:
            discord_embed = DiscordEmbed.warning("이모지 없음", f"`{message.content}`는 이모지 리스트에 없습니다.")
            await message.channel.send(embed=discord_embed, delete_after=10.0)

    # 기존에 작성한 명령어로 이동
    await bot.process_commands(message)


@bot.command(name="도움말", help="이 창을 출력합니다.", usage="`!도움말`")
async def help_command(ctx, func=None):
    await ctx.message.delete()
    cog_list = ["기본 명령어"]  # Cog 리스트 추가
    if func is None:
        embed = discord.Embed(title="이모지 봇 도움말",
                              description="접두사는 `!` 입니다. 자세한 내용은 `!도움말`\0`명령어`를 입력하시면 됩니다.",
                              color=discord.Colour.magenta())  # Embed 생성
        for x in cog_list:  # cog_list에 대한 반복문
            cog_data = bot.get_cog(x)  # x에 대해 Cog 데이터를 구하기
            command_list = cog_data.get_commands()  # cog_data에서 명령어 리스트 구하기
            embed.add_field(name=x, value=" ".join([c.name for c in command_list]), inline=True)  # 필드 추가
        await ctx.send(embed=embed, delete_after=60.0)  # 보내기

    else:  # func가 None이 아니면
        command_notfound = True

        for _title, cog in bot.cogs.items():  # title, cog로 item을 돌려주는데 title은 필요가 없습니다.
            if not command_notfound:  # False면
                break  # 반복문 나가기

            else:  # 아니면
                for title in cog.get_commands():  # 명령어를 아까처럼 구하고 title에 순차적으로 넣습니다.
                    if title.name == func:  # title.name이 func와 같으면
                        cmd = bot.get_command(title.name)  # title의 명령어 데이터를 구합니다.
                        embed = discord.Embed(title=f"명령어 : {cmd}", description=cmd.help,
                                              color=discord.Colour.green())  # Embed 만들기
                        embed.add_field(name="사용법", value=cmd.usage)  # 사용법 추가
                        await ctx.send(embed=embed, delete_after=30.0)  # 보내기
                        command_notfound = False
                        break  # 반복문 나가기
                    else:
                        command_notfound = True
        if command_notfound:  # 명령어를 찾지 못하면
            if func in cog_list:  # 만약 cog_list에 func가 존재한다면
                cog_data = bot.get_cog(func)  # cog 데이터 구하기
                command_list = cog_data.get_commands()  # 명령어 리스트 구하기
                embed = discord.Embed(title=f"카테고리 : {cog_data.qualified_name}",
                                      description=cog_data.description)  # 카테고리 이름과 설명 추가
                embed.add_field(name="명령어들",
                                value=", ".join([c.name for c in command_list]))  # 명령어 리스트 join
                await ctx.send(embed=embed, delete_after=30.0)  # 보내기
            else:
                command_error = discord.Embed(title="명령어 오류", description="다음과 같은 에러가 발생했습니다.",
                                              color=discord.Colour.red())
                command_error.add_field(name="사용한 명령어:\0" + ctx.message.content,
                                        value='`' + ctx.message.content + "`는 없습니다.", inline=False)
                await ctx.send(embed=command_error, delete_after=7.0)


# Cogs 파일(.py)을 로드
@bot.command(name="로드")
@commands.has_permissions(administrator=True)
async def load_commands(extension):
    # 봇 오너
    bot_owner = bot.get_user(276532581829181441)
    bot.load_extension(f"Cogs.{extension}")
    await bot_owner.send(f":white_check_mark: {extension}을(를) 로드했습니다!")


# Cogs 파일(.py)을 언로드
@bot.command(name="언로드")
@commands.has_permissions(administrator=True)
async def unload_commands(extension):
    # 봇 오너
    bot_owner = bot.get_user(276532581829181441)
    bot.unload_extension(f"Cogs.{extension}")
    await bot_owner.send(f":white_check_mark: {extension}을(를) 언로드했습니다!")


# Cogs 파일(.py)을 리로드
@bot.command(name="리로드")
@commands.has_permissions(administrator=True)
async def reload_commands(extension=None):
    # 봇 오너
    bot_owner = bot.get_user(276532581829181441)
    if extension is None:  # extension이 None이면 (그냥 !리로드 라고 썼을 때)
        for filename in os.listdir("Cogs"):
            if filename.endswith(".py"):
                bot.unload_extension(f"Cogs.{filename[:-3]}")
                bot.load_extension(f"Cogs.{filename[:-3]}")
        await bot_owner.send(":white_check_mark: 모든 명령어를 다시 불러왔습니다!")
    else:
        bot.unload_extension(f"Cogs.{extension}")
        bot.load_extension(f"Cogs.{extension}")
        await bot_owner.send(f":white_check_mark: {extension}을(를) 다시 불러왔습니다!")


bot.run('ODI5MzQ2MDA2NjA0MTg1NjAz.YG2yqA.cc2fgvs26QoCmSNzjxGOblb7v14')
