import logging
logger = logging.getLogger(__name__)
from Util import SQLUtil

# global index
guild_emoji_list = []


# 이미지 명령어를 통해 이미지 파일 이름을 구합니다.
class SearchEmojiFileName:
    """이모지 행을 순회하며 명령어와 일치한 파일명을 보관하는 비동기 반복자이다."""
    def __init__(self, length, emoji_tuple_list, emoji_command):
        """순회 길이, (서버 ID, 파일명, 명령어) 목록과 검색어를 저장하고 검색 상태를 초기화한다."""
        self.current = 0
        self.stop = length
        self.emoji_tuple_list = emoji_tuple_list
        self.emoji_command = emoji_command
        self.emoji_file_name = None

    def __aiter__(self):
        """현재 반복자 자신을 반환한다. 이미 진행한 검색 위치는 초기화하지 않는다."""
        return self

    async def __anext__(self):
        """다음 행을 검사하고 현재까지 찾은 파일명 또는 None을 반환한다.

        이전 일치 결과는 계속 유지하며, 지정된 길이에 도달하면 StopAsyncIteration을 발생시킨다.
        """
        logger.debug('%s', f"run async for... current {self.current} until {self.stop}")
        if self.current < self.stop:
            logger.debug('%s %s', self.emoji_tuple_list[self.current][1], self.emoji_command)
            if self.emoji_tuple_list[self.current][2] == self.emoji_command:
                logger.debug('%s', "match!")
                self.emoji_file_name = self.emoji_tuple_list[self.current][1]
            self.current += 1
            return self.emoji_file_name
        else:
            raise StopAsyncIteration


# guild_emoji_list에 있는 GuildEmoji.class를 반환합니다.
class SearchGuildClass:
    """서버 객체 목록을 차례로 검사하여 지정 서버와 일치하는 객체를 찾는 비동기 반복자이다."""
    def __init__(self, length, guild_list, guildID):
        """순회 길이, 서버 객체 목록과 대상 guildID를 저장하고 검색 위치를 초기화한다."""
        self.current = 0
        self.stop = length
        self.guild_list = guild_list
        self.guildID = guildID

    def __aiter__(self):
        """현재 검색 위치를 유지한 채 비동기 반복자 자신을 반환한다."""
        return self

    async def __anext__(self):
        """다음 서버 객체가 대상과 일치하면 객체를, 아니면 None을 반환한다. 끝에서는 StopAsyncIteration을 발생시킨다."""
        logger.debug('%s', f"run async for... current {self.current} until {self.stop}")
        if self.current < self.stop:
            if self.guild_list[self.current].guildID == self.guildID:
                self.current += 1
                return self.guild_list[self.current - 1]
            self.current += 1
            return None
        else:
            raise StopAsyncIteration


# db에 있는 길드 이미지를 램에 로드하기위한 class
class GuildEmoji:
    """서버와 공용 이모지의 DB 행을 메모리에 보관하고 정확한 명령어 검색을 제공한다."""
    def __init__(self, _guildID: int, _global_emoji_list):
        """서버의 DB 이모지 목록을 읽고 전달받은 공용 목록을 추가한다. 서버 목록이 비면 예외가 발생한다."""
        logger.debug('%s', f"new guild emoji class {_guildID}...")
        self.guildID = _guildID
        logger.debug('%s', "load guild emoji command")
        self.emoji_tuple_list = SQLUtil.emoji_search_all(_guildID)
        self.emoji_tuple_list.extend(_global_emoji_list)
        logger.debug('%s %s', self.guildID, self.emoji_tuple_list)

    # 이미지 명령어를 통해 이미지 파일을 반환한다.
    async def emoji_search(self, emoji_command: str):
        """메모리 목록에서 명령어가 정확히 일치하는 첫 파일명을 반환한다. 없으면 None을 반환한다."""
        return next((path for _, path, command in self.emoji_tuple_list if command == emoji_command), None)

    # db와 동기화
    def update_emoji_list(self):
        """메모리 목록을 해당 서버의 최신 DB 행으로 교체한다. 초기 공용 목록은 다시 추가하지 않는다."""
        self.emoji_tuple_list = SQLUtil.emoji_search_all(self.guildID)


# guild_emoji_list에서 guildID와 일치하는 GuildEmoji.class를 반환
async def get_guild_class(_guildID: int):
    """전역 서버 객체 목록에서 _guildID와 일치하는 첫 GuildEmoji를 반환한다. 없으면 None이다."""
    return next((guild for guild in guild_emoji_list if guild.guildID == _guildID), None)
