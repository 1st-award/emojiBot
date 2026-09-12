import asyncio
import discord
import socket

from discord import app_commands
from discord.ext import commands, tasks
from mcstatus import JavaServer

from Util import DiscordEmbed


async def request_server(send_msg=None):
    if send_msg in "start":
        request_type = "서버실행"
    elif send_msg in "stop":
        request_type = "서버종료"

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setblocking(False)
    print("send to server")
    sock.sendto(send_msg.encode(), ("192.168.0.9", 8010))
    print("send success")

    timeout_count = 0
    while timeout_count != 60:
        try:
            print("wait recv to server")
            msg, addr = sock.recvfrom(1500)
            if msg.decode() == "success":
                print("recv success", msg.decode())
                sock.close()
                return DiscordEmbed.info(f"{request_type} 성공!", f"{request_type}이(가) 정상적으로 완료되었습니다!")
            elif msg.decode() == "run or loading":
                if request_type == "서버실행":
                    return DiscordEmbed.warning(f"{request_type} 실패", "이미 서버가 실행되고 있거나 로딩중입니다")
                if request_type == "서버종료":
                    return DiscordEmbed.warning(f"{request_type} 실패", "이미 서버가 종료 되어있습니다")
        except BlockingIOError:
            timeout_count += 1
            await asyncio.sleep(1)
    print("failed request")
    return DiscordEmbed.warning(f"{request_type} 실패", "요청 서버가 닫혀있거나 서버컴이 꺼져있습니다")


class Minecraft(commands.GroupCog, name="마크"):
    def __init__(self, bot):
        self.bot = bot
        super().__init__()
        self.minecraft_stat_check_loop.start()

    @tasks.loop(seconds=10.0)
    async def minecraft_stat_check_loop(self):
        try:
            # Reverse Proxy
            server = await JavaServer.async_lookup("d6aaed0e.secure.mcv.kr:10217")
            # server = await JavaServer.async_lookup("222.103.88.221") # Original IP
            response = server.status()
            if response.players.online == 0:
                msg = "서버 온라인 | !도움말"
            else:
                msg = f"{response.players.online}명이 마인크래프트"
            await self.bot.change_presence(status=discord.Status.online,
                                           activity=discord.Game(name=msg))
        except Exception as e:
            await self.bot.change_presence(status=discord.Status.do_not_disturb, activity=discord.Game(name="!도움말"))

    @minecraft_stat_check_loop.before_loop
    async def wait_bot(self):
        await self.bot.wait_until_ready()

    @app_commands.command(name="실행", description="마인크래프트 서버 실행")
    async def request_server_start(self, interaction: discord.Interaction):
        discord_embed = await request_server("start")
        if discord_embed.title not in "실패":
            await self.bot.change_presence(activity=discord.Game(name="/도움말 마크 서버 ON"))
        await interaction.response.send_message(embed=discord_embed)
        await asyncio.sleep(10)
        await interaction.delete_original_response()

    @app_commands.command(name="서버종료", description="마인크래프트 서버 종료")
    async def request_server_stop(self, interaction: discord.Interaction):
        discord_embed = await request_server("stop")
        if discord_embed.title not in "실패":
            await self.bot.change_presence(activity=discord.Game(name="/도움말"))
        await interaction.response.send_message(embed=discord_embed)
        await asyncio.sleep(10)
        await interaction.delete_original_response()

    # @app_commands.command(name="테스트", description="test")
    # async def request_server_start(self, interaction: discord.Interaction, discord_id: str):
    #     await interaction.response.send_message(self.bot.get_user(int(discord_id)))


async def setup(bot):
    await bot.add_cog(Minecraft(bot))
