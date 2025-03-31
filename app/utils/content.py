from mimetypes import MimeTypes
import os

from aiogram.types import Message, ContentType

from app.config import settings
from app.loader import bot


def message_has_content(message: Message):
    if message.content_type in (
            ContentType.AUDIO,
            ContentType.DOCUMENT,
            ContentType.PHOTO,
            ContentType.VIDEO,
            ContentType.VIDEO_NOTE,
            ContentType.VOICE,
    ):
        return True


def create_content_dir(user_id: int, chat_id: int, message_id: int, date: int) -> str:
    user_dir = os.path.join(settings.CACHE_DIR, str(user_id))
    chat_dir = os.path.join(user_dir, str(chat_id))
    message_dir = os.path.join(chat_dir, str(message_id))
    message_iter_dir = os.path.join(message_dir, str(date))

    if not os.path.exists(settings.CACHE_DIR):
        os.mkdir(settings.CACHE_DIR)
    if not os.path.exists(user_dir):
        os.mkdir(user_dir)
    if not os.path.exists(chat_dir):
        os.mkdir(chat_dir)
    if not os.path.exists(message_dir):
        os.mkdir(message_dir)
    if not os.path.exists(message_iter_dir):
        os.mkdir(message_iter_dir)

    return message_iter_dir


async def download_message_content(message: Message, path: str):
    if message.audio:
        await download_file(message.audio.file_id, message.audio.title, message.audio.mime_type, path)
    if message.document:
        await download_file(message.document.file_id, message.document.title, message.document.mime_type, path)
    if message.photo:
        for photo in message.photo:
            await download_file(photo.file_id, photo.file_id, photo.mime_type, path)
    if message.video:
        await download_file(message.video.file_id, message.video.file_name, message.video.mime_type, path)
    if message.video_note:
        await download_file(message.video_note.file_id, message.video_note.file_id, "video/mp4", path)
    if message.voice:
        await download_file(message.voice.file_id, message.voice.file_id, message.voice.mime_type, path)


async def download_file(file_id: str, filename: str, mimetype: str, path: str):
    if not (extension := MimeTypes().guess_extension(mimetype)):
        extension = "." + mimetype.split("/")[1]
    await bot.download(file=file_id, destination=os.path.join(path, filename + extension))
