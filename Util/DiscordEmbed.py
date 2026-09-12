import discord
from pathlib import Path
from Util.ImojiUtil import emoji_path

def info(_title: str, _description: str = ""):
    """제목과 설명으로 초록색 안내 Embed를 생성해 반환한다."""
    return discord.Embed(title=_title, description=_description, color=discord.Colour.green())


def warning(_title: str, _description: str = ""):
    """제목과 설명으로 빨간색 경고 Embed를 생성해 반환한다."""
    return discord.Embed(title=_title, description=_description, color=discord.Colour.red())


def complete(_title: str, _description: str = ""):
    """제목과 설명으로 파란색 완료 Embed를 생성해 반환한다."""
    return discord.Embed(title=_title, description=_description, color=discord.Colour.blue())


async def picture(_message: discord.Message, _emoji_file_name: str, _is_global_icon=False):
    # 디스코드에 올릴 파일을 지정하고, attachment에서 사용할 이름을 "image.png"로 지정
    """메시지 작성자 정보와 이모지 이미지를 담은 (Embed, Discord 파일)을 반환한다.

    _is_global_icon이 True이면 공용 폴더, 아니면 메시지의 서버 폴더에서
    _emoji_file_name을 연다. 반환한 파일은 전송 후 호출자가 닫아야 한다.
    """
    extension = Path(_emoji_file_name).suffix.lstrip(".")
    user_name = _message.author.display_name
    if user_name is None:
        user_name = _message.author.name
        
    embed = discord.Embed(color=discord.Colour.dark_magenta())
    embed.set_author(name=user_name, icon_url=_message.author.display_avatar.url)
    if _is_global_icon:
        image = discord.File(emoji_path(_emoji_file_name, -1), filename=f"image.{extension}")
        embed.set_image(url=f"attachment://image.{extension}")
    else:
        image = discord.File(emoji_path(_emoji_file_name, _message.guild.id), filename=_emoji_file_name)
        embed.set_image(url=f"attachment://{_emoji_file_name}")
    return embed, image

def bytesIO_image(author, image):
    """작성자 author와 이미지 버퍼 image로 (Embed, Discord 파일)을 반환한다.

    첨부 이름은 generated.png이며 반환한 파일의 수명은 호출자가 관리한다.
    """
    user_name = author.display_name
    if user_name is None:
        user_name = author.name
    # Embed 생성    
    embed = discord.Embed(color=discord.Colour.dark_magenta())
    embed.set_author(name=user_name, icon_url=author.display_avatar.url)
    # Discord 파일로 변환
    file = discord.File(image, filename="generated.png")
    # 첨부파일 이미지를 Embed에 연결
    embed.set_image(url="attachment://generated.png")
    return embed, file

async def emoji_list(_search_result_list: list):
    """(서버 ID, 파일명, 명령어) 행 목록을 이모지 목록 Embed로 변환한다.

    빈 목록은 안내문으로 표시하고, 설명이 Discord 길이 제한을 넘으면 일부만 표시한다.
    """
    description = "\t".join(f"`{row[2]}`" for row in _search_result_list)
    if len(description) > 4096:
        description = description[:4050] + "\n… 일부만 표시합니다."
    return discord.Embed(title="이모지 리스트", description=description or "등록된 이모지가 없습니다.", color=discord.Colour.green())


def rotation_map(current_map: dict, next_map: dict):
    """현재·다음 맵 API 데이터로 맵 이름, 이미지와 교체 시각을 담은 Embed를 반환한다."""
    embed = discord.Embed(title="현재 맵", description=current_map['map'], colour=discord.Colour(0xB93038))
    embed.set_image(url=current_map['asset'])
    embed.add_field(name="시작 시간", value=f"<t:{current_map['start']}:T>\t<t:{current_map['start']}:R>", inline=False)
    embed.add_field(name="종료 시간", value=f"<t:{current_map['end']}:T>\t<t:{current_map['end']}:R>", inline=False)
    embed.add_field(name="다음 맵", value=next_map['map'], inline=False)
    return embed


def rotation_craft(daily_craft: dict, weekly_craft: dict, path):
    """일간·주간 제작 데이터와 이미지 경로로 (제작 일정 Embed, Discord 파일)을 반환한다.

    반환 파일은 전송이 끝난 뒤 호출자가 닫아야 한다.
    """
    image_path = path
    image = discord.File(image_path, filename='craft.png')
    embed = discord.Embed(title="현재 제작", description="", colour=discord.Colour(0xB93038))
    embed.add_field(name='일간 제작 기간', value=f"<t:{daily_craft['start']}:f> ~ <t:{daily_craft['end']}:D>", inline=False)
    embed.add_field(name='주간 제작 기간', value=f"<t:{weekly_craft['start']}:f> ~ <t:{weekly_craft['end']}:D>", inline=False)
    embed.set_image(url="attachment://craft.png")
    return embed, image
