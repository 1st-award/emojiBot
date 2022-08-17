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
        placeholder="선택하세요",
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

    async def on_timeout(self) -> None:
        for child in self.children:
            child.label = "만료된 버튼"
            child.style = discord.ButtonStyle.danger
            child.disable = True
        await self.response.edit(view=self)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        timestamp = discord.utils.format_dt(interaction.created_at, 'F')
        if self.message.author.nick is None:
            author_name = self.message.author.name
        else:
            author_name = self.message.author.nick
        owner = self.bot.get_user(interaction.guild.owner_id)
        embed = DiscordEmbed.warning("신고 접수",
                                     f"신고 유형: {self.report_type.values[0]}\n"
                                     f"신고 일자: {timestamp}\n"
                                     f"상세 내용: {self.report_details.value}\n"
                                     f"신고 대상: {author_name}\n"
                                     f"메시지 내용: {self.message.content}\n"
                                     )
        url_view = LinkButton(label="해당 메시지로 가기", url=self.message.jump_url)
        await owner.send(embed=embed, view=url_view)
        await interaction.response.send_message("신고해 주셔서 감사합니다!", ephemeral=True)


class ReadyButton(discord.ui.View):
    def __init__(self, embed: discord.Embed):
        super().__init__(timeout=None)
        self.count = 0
        self.push_count = 0
        self.current_user = 0
        self.embed = embed

    @discord.ui.button(label="증가", style=discord.ButtonStyle.blurple)
    async def report(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.push_count += 1

        if interaction.user.id == self.current_user and self.push_count > 3:
            self.embed.description = f"<@{interaction.user.id}>님은 3번 누르셨습니다. 현재: {self.count}"
        else:
            if self.push_count > 3 or self.current_user != interaction.user.id:
                self.push_count = 1
            self.count += 1
            self.current_user = interaction.user.id
            self.embed.description = f"<@{interaction.user.id}>님 {self.push_count}. 현재: {self.count}"

        if self.count == 31:
            self.embed.description = f"<@{interaction.user.id}>님 당첨!"
            button.disabled = True
            button.style = discord.ButtonStyle.danger

        await interaction.response.edit_message(embed=self.embed, view=self)


class InviteButton(discord.ui.View):
    def __init__(self, embed: discord.Embed):
        super().__init__(timeout=180)
        self.blue_btn = discord.ui.Button(label="참가", style=discord.ButtonStyle.blurple)
        self.red_btn = discord.ui.Button(label="종료", style=discord.ButtonStyle.red)
        self.add_item(self.blue_btn)
        self.add_item(self.red_btn)
        self.blue_btn.callback = self.invite
        self.red_btn.callback = self.end_invite
        self.embed = embed
        self.players = []

    def switch_label(self):
        self.blue_btn.label = "청팀 승리"
        self.red_btn.label = "홍팀 승리"

    def switch_callback(self):
        self.blue_btn.callback = self.blue_team_win
        self.red_btn.callback = self.red_team_win

    def button_disabled(self):
        self.blue_btn.disabled = True
        self.red_btn.disabled = True

    async def invite(self, interaction: discord.Interaction):
        player_mention = f"<@{interaction.user.id}>"
        if player_mention in self.players:
            embed = DiscordEmbed.warning("중복참여", f"<@{interaction.user.id}>님은 이미 참가하셨습니다.")
            await interaction.response.send_message(embed=embed)
            return
        self.players.append(player_mention)
        self.embed.remove_field(index=0)
        self.embed.add_field(name="참가인원", value=f"{len(self.players)}명", inline=True)
        await interaction.response.edit_message(embed=self.embed, view=self)

    async def end_invite(self, interaction: discord.Interaction):
        if len(self.players) < 2:
            embed = DiscordEmbed.warning("인원 부족", "2명 이상일 때 종료 가능합니다.")
            await interaction.response.send_message(embed=embed)
            return
        self.switch_label()
        self.switch_callback()
        half = len(self.players) // 2
        red_team = self.players[:half]
        blue_team = self.players[half:]
        self.embed = DiscordEmbed.info("팀 결과", "")
        self.embed.add_field(name="청팀", value=" ".join(blue_team), inline=True)
        self.embed.add_field(name="홍팀", value=" ".join(red_team), inline=True)
        await interaction.response.edit_message(embed=self.embed, view=self)

    async def blue_team_win(self, interaction: discord.Interaction):
        self.button_disabled()
        self.embed = DiscordEmbed.info("게임 결과", "청팀 승리!")
        await interaction.response.edit_message(embed=self.embed, view=self)

    async def red_team_win(self, interaction: discord.Interaction):
        self.button_disabled()
        self.embed = DiscordEmbed.info("게임 결과", "홍팀 승리!")
        await interaction.response.edit_message(embed=self.embed, view=self)
