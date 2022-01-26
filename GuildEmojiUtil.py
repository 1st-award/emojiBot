import SQLUtil

# global index
guild_emoji_list = []


# 이미지 명령어를 통해 이미지 파일 이름을 구합니다.
class SearchEmojiFileName:
    def __init__(self, length, emoji_tuple_list, emoji_command):
        self.current = 0
        self.stop = length
        self.emoji_tuple_list = emoji_tuple_list
        self.emoji_command = emoji_command
        self.emoji_file_name = None

    def __aiter__(self):
        return self

    async def __anext__(self):
        print(f"run async for... current {self.current} until {self.stop}")
        if self.current < self.stop:
            print(self.emoji_tuple_list[self.current][1], self.emoji_command)
            if self.emoji_tuple_list[self.current][1] == self.emoji_command:
                print("match!")
                self.emoji_file_name = self.emoji_tuple_list[self.current][0]
            self.current += 1
            return self.emoji_file_name
        else:
            raise StopAsyncIteration


# guild_emoji_list에 있는 GuildEmoji.class를 반환합니다.
class SearchGuildClass:
    def __init__(self, length, guild_list, guildID):
        self.current = 0
        self.stop = length
        self.guild_list = guild_list
        self.guildID = guildID

    def __aiter__(self):
        return self

    async def __anext__(self):
        print(f"run async for... current {self.current} until {self.stop}")
        if self.current < self.stop:
            if self.guild_list[self.current].guildID == self.guildID:
                return self.guild_list[self.current]
            self.current += 1
            return None
        else:
            raise StopAsyncIteration


# db에 있는 길드 이미지를 램에 로드하기위한 class
class GuildEmoji:
    def __init__(self, _guildID: int):
        print(f"new guild emoji class {_guildID}...")
        self.guildID = _guildID
        print("load guild emoji command")
        self.emoji_tuple_list = SQLUtil.emoji_search_all(_guildID)
        print(self.guildID, self.emoji_tuple_list)

    # 이미지 명령어를 통해 이미지 파일을 반환한다.
    async def emoji_search(self, emoji_command: str):
        async for emoji in SearchEmojiFileName(len(self.emoji_tuple_list), self.emoji_tuple_list, emoji_command):
            print("result", emoji)
            if emoji is not None:
                return emoji
        return None

    # db와 동기화
    def update_emoji_list(self):
        self.emoji_tuple_list = SQLUtil.emoji_search_all(self.guildID)


# guild_emoji_list에서 guildID와 일치하는 GuildEmoji.class를 반환
async def get_guild_class(_guildID: int):
    async for guild_class in SearchGuildClass(len(guild_emoji_list), guild_emoji_list, _guildID):
        print("result", guild_class)
        if guild_class is not None:
            return guild_class
    return None
