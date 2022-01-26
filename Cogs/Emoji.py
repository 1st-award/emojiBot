import DiscordEmbed
import ImojiUtil
import SQLUtil
from discord.ext import commands


class Emoji(commands.Cog, name="기본 명령어"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="등록", help="`명령어로 쓸 단어`와 `사진`을 첨부해주세요! (지원 파일: `jpg`, `png`, `gif`)\n"
                                      "GIF 조건 `크기(3MB이하) 해상도(128X128이상)`", usage="`!등록`\t`명령어`\t`사진첨부`")
    async def emoji_register(self, ctx, emoji_command: str):
        await ctx.message.delete()
        print(ctx.message.attachments[0].filename)
        ImojiUtil.is_support_format(ctx.message.attachments[0].filename)
        SQLUtil.emoji_register(ctx.message.attachments[0].filename, emoji_command, ctx.guild.id)
        await ImojiUtil.emoji_save(ctx.message.attachments[0], ctx.guild.id)
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
        await ctx.send(embed=discord_embed, delete_after=30.0)

    @emoji_list.error
    async def emoji_list_error(self, ctx, error: commands.errors.CommandInvokeError):
        if isinstance(error.original, FileNotFoundError):
            discord_embed = DiscordEmbed.warning("이모지 없음", error.original)
        await ctx.send(embed=discord_embed)


def setup(bot):
    bot.add_cog(Emoji(bot))
