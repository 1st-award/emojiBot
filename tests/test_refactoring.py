import asyncio
import sqlite3
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from Util import SQLUtil, EmojiCommands, ImojiUtil, GIFConvert
from PIL import Image


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "test.db"
        with sqlite3.connect(self.path) as db:
            db.executescript("""
                CREATE TABLE guild(guild INTEGER PRIMARY KEY);
                CREATE TABLE emoji(guild INTEGER NOT NULL REFERENCES guild(guild) ON DELETE CASCADE,
                                   path TEXT NOT NULL, command TEXT NOT NULL, PRIMARY KEY(guild, command));
                INSERT INTO guild VALUES (1), (2), (-1);
            """)
        db.close()
        self.patcher = patch.object(SQLUtil, "DB_PATH", self.path)
        self.patcher.start()
        self.addCleanup(self.patcher.stop)

    def test_injection_and_wildcards_are_literals(self):
        for command in ["' OR 1=1 --", "%", "_", "!", "hello"]:
            SQLUtil.register_emoji(command + ".png", command, 1)
            self.assertEqual(SQLUtil.emoji_search(command, 1), (command + ".png",))
        self.assertIsNone(SQLUtil.emoji_search("' OR 1=1 --", 2))
        self.assertIsNone(SQLUtil.emoji_search("", 1))

    def test_exact_delete_and_substring_lookup(self):
        SQLUtil.register_emoji("a.png", "hello world", 1)
        self.assertEqual(SQLUtil.emoji_search("hello", 1), ("a.png",))
        self.assertIsNone(SQLUtil.emoji_search_exact("hello", 1))
        SQLUtil.emoji_remove("hello", 1)
        self.assertIsNotNone(SQLUtil.emoji_search_exact("hello world", 1))

    def test_rollback_batch_and_replace(self):
        SQLUtil.register_emoji("original.png", "original", 1)
        rows = [(1, "a.png", "duplicate"), (1, "b.png", "duplicate")]
        for operation in (SQLUtil.emoji_insert_all, SQLUtil.replace_emoji):
            with self.assertRaises(sqlite3.IntegrityError):
                operation(1, rows)
            self.assertEqual(SQLUtil.emoji_search_all(1), [(1, "original.png", "original")])
        with self.assertRaises(ValueError):
            SQLUtil.emoji_insert_all(1, [(2, "a.png", "other")])

    def test_foreign_keys_and_cascade(self):
        with self.assertRaises(sqlite3.IntegrityError):
            SQLUtil.register_emoji("x.png", "x", 99)
        SQLUtil.register_emoji("a.png", "a", 1)
        SQLUtil.register_emoji("b.png", "b", 2)
        SQLUtil.remove_guild(1)
        self.assertEqual(SQLUtil.emoji_search_all(1, allow_empty=True), [])
        self.assertEqual(len(SQLUtil.emoji_search_all(2)), 1)

    def test_random_empty_global_and_local_precedence(self):
        self.assertIsNone(EmojiCommands.resolve_emoji("랜덤", 1))
        SQLUtil.register_emoji("global.png", "same", -1)
        self.assertEqual(EmojiCommands.resolve_emoji("랜덤", 1), ("global.png", True))
        SQLUtil.register_emoji("local.png", "same", 1)
        self.assertEqual(EmojiCommands.resolve_emoji("same", 1), ("local.png", False))

    def test_duplicate_and_thread_access(self):
        SQLUtil.register_emoji("a.png", "a", 1)
        with self.assertRaises(FileExistsError):
            SQLUtil.register_emoji("b.png", "a", 1)
        result = asyncio.run(asyncio.to_thread(SQLUtil.emoji_search, "a", 1))
        self.assertEqual(result, ("a.png",))


class UtilityTests(unittest.TestCase):
    def test_paths_and_attachment_types(self):
        for path in ("../emoji.db", "../../.env", "sub/file.png"):
            with self.assertRaises(ValueError):
                ImojiUtil.emoji_path(path, 1)
        self.assertEqual(ImojiUtil.attachment_filename(SimpleNamespace(id=5, content_type="image/jpeg")), "5.jpg")
        with self.assertRaises(NotImplementedError):
            ImojiUtil.attachment_filename(SimpleNamespace(id=5, content_type=None))

    def test_gif_resize_preserves_loop_and_duration(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "test.gif"
            frames = [Image.new("RGB", (40, 40), color) for color in ("red", "blue")]
            frames[0].save(path, save_all=True, append_images=frames[1:], loop=3, duration=[100, 200])
            for frame in frames:
                frame.close()
            GIFConvert.scale_gif(path, (20, 20))
            with Image.open(path) as image:
                self.assertEqual(image.size, (20, 20))
                self.assertEqual(image.info["loop"], 3)
                self.assertEqual(image.info["duration"], 100)
                image.seek(1)
                self.assertEqual(image.info["duration"], 200)


class MessageTests(unittest.IsolatedAsyncioTestCase):
    async def test_prefix_removed_only_once_and_file_closed(self):
        message = SimpleNamespace(content="~a~b", guild=SimpleNamespace(id=1),
                                  delete=AsyncMock(), channel=SimpleNamespace(send=AsyncMock()), reference=None)
        file = SimpleNamespace(close=lambda: None)
        from unittest.mock import Mock
        file.close = Mock()
        with patch.object(EmojiCommands, "resolve_emoji", return_value=("a.png", False)) as resolve:
            with patch.object(EmojiCommands.DiscordEmbed, "picture", new=AsyncMock(return_value=(None, file))):
                await EmojiCommands.handle_emoji_message(message)
        resolve.assert_called_once_with("a~b", 1)
        file.close.assert_called_once()

    async def test_empty_command_is_ignored(self):
        message = SimpleNamespace(content="~  ", delete=AsyncMock())
        await EmojiCommands.handle_emoji_message(message)
        message.delete.assert_not_called()


if __name__ == "__main__":
    unittest.main()
