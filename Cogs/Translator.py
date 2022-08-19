import json
import os
import urllib.request

from discord import app_commands, Locale


class Translator(app_commands.Translator):
    async def translate(self,
                        word: app_commands.locale_str,
                        locale: Locale,
                        context: app_commands.TranslationContext):
        available_language = ['ko', 'en', 'ja', 'zh-CN', 'zh-TW', 'vi', 'id', 'th', 'ru', 'es']
        if str(locale) not in available_language:
            return None

        client_id = os.environ['CLIENT_ID']
        client_secret = os.environ['CLIENT_SECRET']
        quote = urllib.parse.quote(word.message)
        url = "https://openapi.naver.com/v1/papago/n2mt"
        data = f"source=en&target={locale}&text={quote}"
        print(data)
        request = urllib.request.Request(url)
        request.add_header("X-Naver-Client-Id", client_id)
        request.add_header("X-Naver-Client-Secret", client_secret)
        response = urllib.request.urlopen(request, data=data.encode("utf-8"))
        code = response.getcode()
        if code == 200:
            body = response.read()
            decode = json.loads(body.decode("utf-8"))
            trans_word = decode["message"]["result"]["translatedText"].replace('.', '').replace(' ', '')
            print(trans_word)
            return trans_word
        return None


async def setup(bot):
    await bot.tree.set_translator(Translator())
