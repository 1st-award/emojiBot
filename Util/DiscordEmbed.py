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
    embed.set_author(name=user_name, icon_url=_message.author.avatar.url)
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
