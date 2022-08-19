import discord


def info(_title: str, _description: str = ""):
    return discord.Embed(title=_title, description=_description, color=discord.Colour.green())


def warning(_title: str, _description: str = ""):
    return discord.Embed(title=_title, description=_description, color=discord.Colour.red())


def complete(_title: str, _description: str = ""):
    return discord.Embed(title=_title, description=_description, color=discord.Colour.blue())


async def picture(_message: discord.Message, _emoji_file_name: str, image=None):
    # 디스코드에 올릴 파일을 지정하고, attachment에서 사용할 이름을 "image.png"로 지정
    user_name = _message.author.nick
    if user_name is None:
        user_name = _message.author.name
    embed = discord.Embed(color=discord.Colour.dark_magenta())
    embed.set_author(name=user_name, icon_url=_message.author.display_avatar.url)
    if _emoji_file_name.startswith("https") or _emoji_file_name.startswith("http"):
        embed.set_image(url=_emoji_file_name)
    else:
        image = discord.File(f"Emoji/{_message.guild.id}/{_emoji_file_name}", filename=_emoji_file_name)
        embed.set_image(url=f"attachment://{_emoji_file_name}")
    return embed, image


async def emoji_list(_search_result_list: list):
    print("start make emoji list...")

    class IndexCommand:
        def __init__(self, length):
            self.current = 0
            self.stop = length
            self.emoji_command_str = ""

        def __aiter__(self):
            return self

        async def __anext__(self):
            print(f"run async for...current {self.current} until {self.stop}")
            if self.current < self.stop:
                self.emoji_command_str += "`" + _search_result_list[self.current][2] + "`\t"
                self.current += 1
                return self.emoji_command_str
            else:
                raise StopAsyncIteration

    async for emoji_num in IndexCommand(len(_search_result_list)):
        emoji_command_str = emoji_num

    embed = discord.Embed(title="이모지 리스트", description=emoji_command_str, color=discord.Colour.green())
    print("return discord embed...")
    return embed


def rotation_map(current_map: dict, next_map: dict):
    embed = discord.Embed(title="현재 맵", description=current_map['map'], colour=discord.Colour(0xB93038))
    embed.set_image(url=current_map['asset'])
    embed.add_field(name="시작 시간", value=f"<t:{current_map['start']}:T>\t<t:{current_map['start']}:R>", inline=False)
    embed.add_field(name="종료 시간", value=f"<t:{current_map['end']}:T>\t<t:{current_map['end']}:R>", inline=False)
    embed.add_field(name="다음 맵", value=next_map['map'], inline=False)
    return embed


def rotation_craft(daily_craft: dict, weekly_craft: dict, path):
    image_path = path
    image = discord.File(image_path, filename='craft.png')
    embed = discord.Embed(title="현재 제작", description="", colour=discord.Colour(0xB93038))
    embed.add_field(name='일간 제작 기간', value=f"<t:{daily_craft['start']}:f> ~ <t:{daily_craft['end']}:D>", inline=False)
    embed.add_field(name='주간 제작 기간', value=f"<t:{weekly_craft['start']}:f> ~ <t:{weekly_craft['end']}:D>", inline=False)
    embed.set_image(url="attachment://craft.png")
    return embed, image
