import functools
from Util import DiscordEmbed, ImojiUtil, SQLUtil
from discord.ext import commands


class Emoji(commands.Cog, name="기본 명령어"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="등록", help="`명령어로 쓸 단어`와 `사진`을 첨부해주세요! (지원 파일: `jpg`, `png`, `gif`)\n"
                                      "GIF 조건 `크기(3MB이하) 해상도(128X128이상)`", usage="`!등록`\t`명령어`\t`사진첨부`")
    async def emoji_register(self, ctx, *emoji_commands: tuple, emoji_command: str = ""):
        for command in emoji_commands:
            emoji_command += ', '.join(command)
        await ctx.message.delete()
        file_type = ctx.message.attachments[0].content_type.split("/")
        file_name = str(ctx.message.attachments[0].id) + "." + file_type[1]

        ImojiUtil.is_support_format(ctx.message.attachments[0].filename)
        SQLUtil.register_emoji(file_name, emoji_command, ctx.guild.id)
        await ImojiUtil.save_emoji(ctx.message.attachments[0], ctx.guild.id)
        discord_embed = DiscordEmbed.info("등록 완료", f"{emoji_command}이(가) 등록되었습니다.")
        await ctx.send(embed=discord_embed, delete_after=5.0)

    @emoji_register.error
    async def emoji_register_error(self, ctx, error: commands.errors.CommandInvokeError, discord_embed=None):
        if isinstance(error.original, IndexError):
            discord_embed = DiscordEmbed.warning("사진 없음", "등록해야 할 사진이 없습니다.")
        elif isinstance(error.original, NotImplementedError):
            discord_embed = DiscordEmbed.warning("지원하지 않는 파일", error.original)
        elif isinstance(error.original, FileExistsError):
            discord_embed = DiscordEmbed.warning("중복 명령어", error.original)
        elif isinstance(error.original, ValueError):
            discord_embed = DiscordEmbed.warning("GIF 변환 실패", error.original)
            # gif 변환 실패로인한 db에서의 명령어와 gif 삭제
            emoji_command = ctx.message.content.split()
            SQLUtil.emoji_remove(emoji_command[-1], ctx.guild.id)
            ImojiUtil.emoji_remove(ctx.message.attachments[0].filename, ctx.guild.id)
        await ctx.send(embed=discord_embed, delete_after=15.0)

    @commands.command(name="삭제", help="`지울 명령어`를 입력해 주세요!", usage="`!삭제`\t`명령어`")
    async def emoji_remove(self, ctx, emoji_command: str):
        await ctx.message.delete()
        search_result_arg = SQLUtil.emoji_search(emoji_command, ctx.guild.id)
        if isinstance(search_result_arg, tuple):
            SQLUtil.emoji_remove(emoji_command, ctx.guild.id)
            ImojiUtil.emoji_remove(search_result_arg[0], ctx.guild.id)
            discord_embed = DiscordEmbed.info("삭제 완료", f"{emoji_command}이(가) 삭제되었습니다.")
            await ctx.send(embed=discord_embed, delete_after=5.0)
        else:
            raise FileNotFoundError(f"`{emoji_command}`는(은) 명령어로 등록되어있지 않습니다.")

    @emoji_remove.error
    async def emoji_remove_error(self, ctx, error: commands.errors.CommandInvokeError):
        if isinstance(error.original, FileNotFoundError):
            discord_embed = DiscordEmbed.warning("삭제 오류", error.original)
        elif isinstance(error.original, PermissionError):
            discord_embed = DiscordEmbed.warning("삭제 실패", "현재 사용 중인 이모지이므로 잠시 후 다시 시도해 주세요.")
        await ctx.send(embed=discord_embed, delete_after=5.0)

    @commands.command(name="리스트", help="서버에 등록되어있는 모든 이모지 명령어를 보여줍니다.", usage="`!리스트`")
    async def emoji_list(self, ctx):
        await ctx.message.delete()
        search_result = SQLUtil.emoji_search_all(ctx.guild.id)
        print(type(search_result), search_result)
        discord_embed = await DiscordEmbed.emoji_list(ctx.message, search_result)
        await ctx.send(embed=discord_embed, delete_after=300.0)

    @emoji_list.error
    async def emoji_list_error(self, ctx, error: commands.errors.CommandInvokeError):
        if isinstance(error.original, FileNotFoundError):
            discord_embed = DiscordEmbed.warning("이모지 없음", error.original)
        await ctx.send(embed=discord_embed)

    @commands.command(name="디시콘", help="펀가놈의 디시콘을 사용할 수 있습니다.", usage="`~`\t`펀가놈 디시콘 명령어`")
    async def funz_list(self, ctx):
        await ctx.message.delete()
        discord_embed = DiscordEmbed.info("펀 가 이 동", "디시콘 명령어 리스트\n`~`\t`디시콘 명령어`로 사용할 수 있습니다"
                                                     "\nhttps://funzinnu.com/dccon.html")
        await ctx.send(embed=discord_embed, delete_after=300.0)

    @commands.command(name="랜덤", help="이모지 중 무작위 하나를 보여줍니다.", usage="`~랜덤`")
    async def random_emoji(self, ctx):
        await ctx.message.delete()
        discord_embed = DiscordEmbed.warning("`~랜덤`을 사용해주세요.", "")
        await ctx.send(embed=discord_embed, delete_after=10.0)

    @commands.command(name="복사", usage="`!복사`\t`To 길드ID`\t`From 길드ID`")
    @commands.has_permissions(administrator=True)
    async def copy_imoji(self, ctx, toGuildID: int, fromGuildID: int):
        await ctx.message.delete()
        SQLUtil.remove_guild(fromGuildID)
        SQLUtil.insert_guild(fromGuildID)
        imoji_args = SQLUtil.emoji_search_all(toGuildID)
        imoji_args = list(map(functools.partial(self.switch_guild, guild=fromGuildID), imoji_args))
        SQLUtil.emoji_insert_all(fromGuildID, imoji_args)
        ImojiUtil.emoji_dir_copy(toGuildID, fromGuildID)
        discord_embed = DiscordEmbed.info("복사 완료")
        await ctx.send(embed=discord_embed, delete_after=3.0)

    @copy_imoji.error
    async def merge_imoji_error(self, ctx, error: commands.errors.CommandInvokeError):
        discord_embed = DiscordEmbed.warning("머지 애러 발생", error.__traceback__)
        await ctx.send(embed=discord_embed, delete_after=5.0)

    def switch_guild(self, imoji: tuple, guild: int):
        list_imoji = list(imoji)
        list_imoji[0] = guild
        return tuple(list_imoji)


def setup(bot):
    bot.add_cog(Emoji(bot))
