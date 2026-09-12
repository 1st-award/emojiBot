import asyncio
import discord.ui
from discord import Interaction
from discord.ext import commands
from Util import DiscordEmbed


class LinkButton(discord.ui.View):
    """지정 URL을 여는 링크 버튼 하나를 표시하는 Discord View이다."""
    def __init__(self, label: str, url: str):
        """표시 문구 label과 이동 주소 url로 링크 버튼을 생성한다."""
        super().__init__()
        self.add_item(discord.ui.Button(label=label, url=url))


class ReportButton(discord.ui.View):
    """저장된 명령어 오류를 봇 제작자에게 전송하는 버튼 View이다."""
    def __init__(self, bot: commands.Bot, error: discord.app_commands.AppCommandError):
        """오류를 전송할 bot과 보고할 error를 보관한다."""
        super().__init__()
        self.bot = bot
        self.error = error

    @discord.ui.button(label="제작자 일 시키기", style=discord.ButtonStyle.danger)
    async def report(self, interaction: Interaction, button: discord.ui.Button):
        """버튼 클릭 시 오류를 제작자에게 보내고 버튼을 비활성화한다. 응답은 5초 뒤 삭제한다."""
        bot_owner = self.bot.get_user(276532581829181441)
        embed = DiscordEmbed.warning("애러발생 일해라 ㅠ", self.error)
        await bot_owner.send(embed=embed)
        button.label = "전송완료"
        button.disabled = True

        await interaction.response.edit_message(view=self)
        await asyncio.sleep(5)
        await interaction.delete_original_response()


class ReportModal(discord.ui.Modal, title="신고"):
    """메시지 신고 사유와 상세 내용을 받아 서버 소유자에게 전달하는 모달이다."""
    def __init__(self, bot: commands.Bot, message: discord.Message):
        """신고 전달에 사용할 bot과 신고 대상 message를 보관한다."""
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
        """입력 제한 시간이 지나면 모달의 이벤트 처리를 종료한다."""
        self.stop()

    async def on_submit(self, interaction: Interaction) -> None:
        """신고 내용·대상·메시지 링크를 서버 소유자에게 보내고 신고자에게 비공개 응답을 보낸다."""
        timestamp = discord.utils.format_dt(interaction.created_at, 'F')
        if self.message.author.display_name is None:
            author_name = self.message.author.name
        else:
            author_name = self.message.author.display_name
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
    """숫자를 증가시키며 31번째 클릭 사용자를 표시하는 게임 버튼 View이다."""
    def __init__(self, embed: discord.Embed):
        """게임 결과를 표시할 embed를 보관하고 누적 횟수와 사용자별 연속 클릭 상태를 초기화한다."""
        super().__init__(timeout=None)
        self.count = 0
        self.push_count = 0
        self.current_user = 0
        self.embed = embed

    @discord.ui.button(label="증가", style=discord.ButtonStyle.blurple)
    async def report(self, interaction: Interaction, button: discord.ui.Button):
        """클릭 횟수를 반영해 메시지를 갱신한다. 같은 사용자의 연속 증가는 세 번까지 허용한다.

        전체 횟수가 31이 되면 해당 사용자를 표시하고 버튼을 비활성화한다.
        """
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
    """참가자를 모집하고 두 팀 배정과 승리 결과를 표시하는 버튼 View이다."""
    def __init__(self, embed: discord.Embed):
        """참가 현황용 embed와 참가·종료 버튼을 생성하고 참가자 목록을 초기화한다."""
        super().__init__(timeout=180)
        self.blue_team = None
        self.red_team = None
        self.blue_btn = discord.ui.Button(label="참가", style=discord.ButtonStyle.blurple)
        self.red_btn = discord.ui.Button(label="종료", style=discord.ButtonStyle.red)
        self.add_item(self.blue_btn)
        self.add_item(self.red_btn)
        self.blue_btn.callback = self.invite
        self.red_btn.callback = self.end_invite
        self.embed = embed
        self.players = []

    def switch_label(self):
        """참가·종료 버튼의 문구를 청팀 승리·홍팀 승리로 변경한다."""
        self.blue_btn.label = "청팀 승리"
        self.red_btn.label = "홍팀 승리"

    def switch_callback(self):
        """두 버튼의 동작을 각각 청팀·홍팀 승리 처리 함수로 변경한다."""
        self.blue_btn.callback = self.blue_team_win
        self.red_btn.callback = self.red_team_win

    def button_disabled(self):
        """참가 또는 승리 선택에 사용하는 두 버튼을 모두 비활성화한다."""
        self.blue_btn.disabled = True
        self.red_btn.disabled = True

    async def invite(self, interaction: Interaction):
        """클릭 사용자를 참가자 목록에 추가하고 인원수를 갱신한다. 중복 참가에는 경고를 응답한다."""
        player_mention = f"<@{interaction.user.id}>"
        if player_mention in self.players:
            embed = DiscordEmbed.warning("중복참여", f"<@{interaction.user.id}>님은 이미 참가하셨습니다.")
            await interaction.response.send_message(embed=embed)
            return
        self.players.append(player_mention)
        self.embed.remove_field(index=0)
        self.embed.add_field(name="참가인원", value=f"{len(self.players)}명", inline=True)
        await interaction.response.edit_message(embed=self.embed, view=self)

    async def end_invite(self, interaction: Interaction):
        """두 명 이상이면 모집을 종료하고 참가 순서에 따라 목록을 절반으로 나눠 팀을 표시한다.

        홀수 인원에서 청팀이 한 명 더 많으며, 버튼은 승리 팀 선택 용도로 전환한다.
        """
        if len(self.players) < 2:
            embed = DiscordEmbed.warning("인원 부족", "2명 이상일 때 종료 가능합니다.")
            await interaction.response.send_message(embed=embed)
            return
        self.switch_label()
        self.switch_callback()
        half = len(self.players) // 2
        self.red_team = self.players[:half]
        self.blue_team = self.players[half:]
        self.embed = DiscordEmbed.info("팀 결과", "")
        self.embed.add_field(name="청팀", value=" ".join(self.blue_team), inline=True)
        self.embed.add_field(name="홍팀", value=" ".join(self.red_team), inline=True)
        await interaction.response.edit_message(embed=self.embed, view=self)

    async def blue_team_win(self, interaction: Interaction):
        """청팀 승리와 팀원을 표시하고 결과 선택 버튼을 비활성화한다."""
        self.button_disabled()
        self.embed = DiscordEmbed.info("게임 결과", "")
        self.embed.add_field(name="청팀 승리!", value=" ".join(self.blue_team), inline=True)
        await interaction.response.edit_message(embed=self.embed, view=self)

    async def red_team_win(self, interaction: Interaction):
        """홍팀 승리와 팀원을 표시하고 결과 선택 버튼을 비활성화한다."""
        self.button_disabled()
        self.embed = DiscordEmbed.info("게임 결과", "")
        self.embed.add_field(name="홍팀 승리!", value=" ".join(self.red_team), inline=True)
        await interaction.response.edit_message(embed=self.embed, view=self)


class News(discord.ui.View):
    """뉴스 목록을 앞·뒤 페이지 버튼과 원문 링크로 탐색하는 Discord View이다."""
    def __init__(self, embed: discord.Embed, news_list: list):
        """표시할 embed와 뉴스 목록으로 페이지 이동 버튼을 생성한다.

        news_list는 비어 있으면 안 되며 각 항목에 link, title, short_desc, img가 필요하다.
        시간 만료 시 삭제할 응답은 호출자가 interaction 속성에 지정한다.
        """
        super().__init__(timeout=3600)
        self.interaction: Interaction = None
        self.embed = embed
        self.news_list = news_list
        self.current_page = 0
        if not news_list:
            raise ValueError("뉴스 목록이 비어 있습니다.")
        self.max_page = len(news_list) - 1

        self.front_btn = discord.ui.Button(emoji="\u23EE", style=discord.ButtonStyle.blurple, disabled=True)
        self.previous_btn = discord.ui.Button(emoji="\u25C0", style=discord.ButtonStyle.blurple, disabled=True)
        self.next_btn = discord.ui.Button(emoji="\u25B6", style=discord.ButtonStyle.blurple)
        self.back_btn = discord.ui.Button(emoji="\u23ED", style=discord.ButtonStyle.blurple)
        self.link_btn = discord.ui.Button(label="자세히", style=discord.ButtonStyle.link, url=news_list[0]['link'], row=1)

        self.add_item(self.front_btn)
        self.add_item(self.previous_btn)
        self.add_item(self.next_btn)
        self.add_item(self.back_btn)
        self.add_item(self.link_btn)

        self.front_btn.callback = self.push_front
        self.previous_btn.callback = self.push_prev
        self.next_btn.callback = self.push_next
        self.back_btn.callback = self.push_back
        self._check_active_btn()

    async def on_timeout(self) -> None:
        """View 시간이 만료되면 저장된 interaction의 원본 응답을 삭제한다. 지정되지 않았으면 무시한다."""
        if self.interaction is not None:
            await self.interaction.delete_original_response()

    def _set_embed(self):
        """현재 페이지의 뉴스 제목·요약·이미지와 원문 링크를 화면 구성 요소에 반영한다."""
        self.embed.title = self.news_list[self.current_page]['title']
        self.embed.description = self.news_list[self.current_page]['short_desc']
        self.embed.set_image(url=self.news_list[self.current_page]['img'])
        self.link_btn.url = self.news_list[self.current_page]['link']

    def _check_active_btn(self):
        """첫 페이지와 마지막 페이지 여부에 따라 이전·다음 이동 버튼을 활성화하거나 비활성화한다."""
        self.front_btn.disabled = self.previous_btn.disabled = self.current_page == 0
        self.next_btn.disabled = self.back_btn.disabled = self.current_page == self.max_page

    async def push_front(self, interaction: Interaction):
        """첫 뉴스 페이지로 이동하고 Embed와 버튼 상태를 갱신해 응답한다."""
        self.current_page = 0
        self._check_active_btn()
        self._set_embed()
        await interaction.response.edit_message(embed=self.embed, view=self)

    async def push_prev(self, interaction: Interaction):
        """첫 페이지보다 앞서지 않도록 이전 뉴스로 이동한 뒤 메시지를 갱신한다."""
        self.current_page = max(0, self.current_page - 1)
        self._check_active_btn()
        self._set_embed()
        await interaction.response.edit_message(embed=self.embed, view=self)

    async def push_next(self, interaction: Interaction):
        """마지막 페이지를 넘지 않도록 다음 뉴스로 이동한 뒤 메시지를 갱신한다."""
        self.current_page = min(self.max_page, self.current_page + 1)
        self._check_active_btn()
        self._set_embed()
        await interaction.response.edit_message(embed=self.embed, view=self)

    async def push_back(self, interaction: Interaction):
        """마지막 뉴스 페이지로 이동하고 Embed와 버튼 상태를 갱신해 응답한다."""
        self.current_page = self.max_page
        self._check_active_btn()
        self._set_embed()
        await interaction.response.edit_message(embed=self.embed, view=self)
