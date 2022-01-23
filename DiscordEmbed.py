import discord


def info(_title: str, _description: str):
    return discord.Embed(title=_title, description=_description, color=discord.Colour.green())


def warning(_title: str, _description: str):
    return discord.Embed(title=_title, description=_description, color=discord.Colour.red())


def complete(_title: str, _description: str):
    return discord.Embed(title=_title, description=_description, color=discord.Colour.blue())


async def picture(message: discord.Message, _emoji_file_name: str):
    # 디스코드에 올릴 파일을 지정하고, attachment에서 사용할 이름을 "image.png"로 지정
    image = discord.File(f"Emoji/{message.guild.id}/{_emoji_file_name}", filename=_emoji_file_name)

    embed = discord.Embed(color=discord.Colour.dark_magenta())
    embed.set_author(name=message.author.name, icon_url=message.author.avatar_url)
    embed.set_image(url=f"attachment://{_emoji_file_name}")
    return embed, image
