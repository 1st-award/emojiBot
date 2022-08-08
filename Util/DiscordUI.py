import asyncio
import discord.ui
from discord.ext import commands
from Util import DiscordEmbed


class LinkButton(discord.ui.View):
    def __init__(self, label: str, url: str):
        super().__init__()
        self.add_item(discord.ui.Button(label=label, url=url))


class ReportButton(discord.ui.View):
    def __init__(self, bot: commands.Bot, error: discord.app_commands.AppCommandError):
        super().__init__()
        self.bot = bot
        self.error = error

    @discord.ui.button(label="제작자 일 시키기", style=discord.ButtonStyle.danger)
    async def report(self, interaction: discord.Interaction, button: discord.ui.Button):
        bot_owner = self.bot.get_user(276532581829181441)
        embed = DiscordEmbed.warning("애러발생 일해라 ㅠ", self.error)
        await bot_owner.send(embed=embed)
        button.label = "전송완료"
        button.disabled = True

        await interaction.response.edit_message(view=self)
        await asyncio.sleep(5)
        await interaction.delete_original_message()


class ReportModal(discord.ui.Modal, title="신고"):
    def __init__(self, bot: commands.Bot, message: discord.Message):
        super().__init__()
        self.bot = bot
        self.message = message

    report_type = discord.ui.Select(
        options=[discord.SelectOption(label="욕설"),
                 discord.SelectOption(label="성희롱"),
                 discord.SelectOption(label="채팅 도배"),
                 discord.SelectOption(label="기타")
                 ]
    )

    report_details = discord.ui.TextInput(
        label="상세사항",
        style=discord.TextStyle.long,
        placeholder="있었던 일을 그대로 써 주세요.",
        required=False,
        max_length=300,
    )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        timestamp = discord.utils.format_dt(interaction.created_at, 'F')
        if self.message.author.nick is None:
            author_name = self.message.author.name
        else:
            author_name = self.message.author.nick
        owner = self.bot.get_user(interaction.guild.owner_id)
        embed = DiscordEmbed.warning("신고 접수", f"신고 유형: {self.report_type.values[0]}\n"
                                              f"신고 일자: {timestamp}\n"
                                              f"상세 내용: {self.report_details.value}\n"
                                              f"신고 대상: {author_name}\n"
                                              f"메시지 내용: {self.message.content}\n"
                                     )
        url_view = LinkButton(label="해당 메시지로 가기", url=self.message.jump_url)
        await owner.send(embed=embed, view=url_view)
        await interaction.response.send_message("신고해 주셔서 감사합니다!", ephemeral=True)
