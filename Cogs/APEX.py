import asyncio
from datetime import datetime

import discord.utils
from discord import app_commands, Interaction
from discord.app_commands import Choice
from discord.ext import commands, tasks

from Util import DiscordEmbed, DiscordUI, APEXUtil


class APEX(commands.GroupCog, name="에펙"):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        self.news_list = None
        self.current_map = None
        self.next_map = None
        self.daily_craft = None
        self.weekly_craft = None
        self.craft_img_path = None

        self.get_news.start()
        self.get_rotation_map.start()
        self.get_craft_rotation.start()

    def cog_unload(self) -> None:
        self.get_news.cancel()
        self.get_rotation_map.cancel()
        self.get_craft_rotation.cancel()

    @tasks.loop(hours=1.0)
    async def get_news(self):
        self.news_list = APEXUtil.get_news()

    @tasks.loop()
    async def get_rotation_map(self):
        self.current_map, self.next_map = APEXUtil.get_rotation_map()
        end_timestamp = self.current_map['end'] + 3
        end_date_time = datetime.fromtimestamp(end_timestamp)
        await discord.utils.sleep_until(end_date_time)

    @tasks.loop()
    async def get_craft_rotation(self):
        self.daily_craft, self.weekly_craft = APEXUtil.get_crafts()
        end_timestamp = self.daily_craft['end'] + 3
        end_date_time = datetime.fromtimestamp(end_timestamp)
        self.craft_img_path = await APEXUtil.create_rotation_craft_img(self.daily_craft, self.weekly_craft)
        await discord.utils.sleep_until(end_date_time)

    @get_news.before_loop
    @get_rotation_map.before_loop
    @get_craft_rotation.before_loop
    async def bot_wait_loop(self):
        await self.bot.wait_until_ready()

    @app_commands.command(name="뉴스", description="최근 에이펙스 뉴스를 보여줍니다.")
    async def show_news(self, interaction: Interaction):
        embed = DiscordEmbed.info(self.news_list[0]['title'], self.news_list[0]['short_desc'])
        embed.set_image(url=self.news_list[0]['img'])
        news = DiscordUI.News(embed, self.news_list)
        news.interaction = interaction
        await interaction.response.send_message(embed=embed, view=news)

    @app_commands.command(name="로테이션")
    @app_commands.rename(rotation_type="유형")
    @app_commands.choices(
        rotation_type=[
            Choice(name="맵", value="map"),
            Choice(name="제작", value="craft"),
        ]
    )
    async def show_rotation(self, interaction: Interaction, rotation_type: Choice[str]):
        image = discord.utils.MISSING
        if rotation_type.value == "map":
            embed = DiscordEmbed.rotation_map(self.current_map, self.next_map)
        elif rotation_type.value == "craft":
            embed, image = DiscordEmbed.rotation_craft(self.daily_craft, self.weekly_craft, self.craft_img_path)
        await interaction.response.send_message(embed=embed, file=image)
        await asyncio.sleep(3600)
        await interaction.delete_original_message()


async def setup(bot):
    await bot.add_cog(APEX(bot))
