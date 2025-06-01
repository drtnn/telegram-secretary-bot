import asyncio
import logging
import os
from datetime import datetime, timedelta
from mimetypes import MimeTypes
from typing import Union, Optional

from aiogram.types import Message, ContentType, BusinessConnection, FSInputFile, InputMediaAudio, InputMediaDocument, \
    InputMediaPhoto, InputMediaVideo, InlineKeyboardMarkup, Chat

from app.config import settings
from app.database.models import UserPeerMessage, User
from app.loader import bot, user_peer_message_repository, storage
from app.utils.markups import user_link_markup
from app.utils.patterns import EDIT_MESSAGE_TEXT, BEFORE_EDIT_MESSAGE_TEXT, AFTER_EDIT_MESSAGE_TEXT, \
    DELETE_MESSAGE_TEXT, DELETE_VIDEO_NOTE_MESSAGE_TEXT

logger = logging.getLogger(__name__)

MEDIA_TYPES = (
    ContentType.AUDIO,
    ContentType.DOCUMENT,
    ContentType.PHOTO,
    ContentType.VIDEO,
    ContentType.VIDEO_NOTE,
    ContentType.VOICE,
)

MEDIA_GROUP_TYPES = (
    ContentType.AUDIO,
    ContentType.DOCUMENT,
    ContentType.PHOTO,
    ContentType.VIDEO,
)

NOTE_TYPES = (
    ContentType.VIDEO_NOTE,
    ContentType.VOICE,
)


async def save_message(message: Message, business_connection: BusinessConnection) -> UserPeerMessage:
    user_peer_message = UserPeerMessage(
        user_id=business_connection.user.id,
        chat_id=message.chat.id,
        message_id=message.message_id,
        message=message.model_dump_json(exclude_none=True),
        text=message.text or message.caption,
        type=message.content_type,
        created_at=message.date.date(),
        updated_at=datetime.now()
    )

    if message_has_content(message):
        path_to_files = create_content_dir(
            user_id=business_connection.user.id, chat_id=message.chat.id, message_id=message.message_id,
            date=int(datetime.now().timestamp())
        )
        user_peer_message = await download_message_content(user_peer_message, message, path_to_files)

    return await user_peer_message_repository.create(user_peer_message)


def message_has_content(message: Message):
    return True if message.content_type in MEDIA_TYPES else False


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


async def download_message_content(user_peer_message: UserPeerMessage, message: Message, path: str) -> UserPeerMessage:
    if message.audio:
        user_peer_message.file_id = message.audio.file_id
        user_peer_message.filename = message.audio.file_name
        user_peer_message.mimetype = message.audio.mime_type
        user_peer_message.filepath = os.path.join(path, user_peer_message.filename)

    if message.document:
        user_peer_message.file_id = message.document.file_id
        user_peer_message.filename = message.document.file_name
        user_peer_message.mimetype = message.document.mime_type
        user_peer_message.filepath = os.path.join(path, user_peer_message.filename)

    if message.photo:
        user_peer_message.file_id = message.photo[-1].file_id
        user_peer_message.filename = get_filename(message.photo[-1].file_id, "image/jpeg")
        user_peer_message.mimetype = "image/jpeg"
        user_peer_message.filepath = os.path.join(path, user_peer_message.filename)

    if message.video:
        user_peer_message.file_id = message.video.file_id
        user_peer_message.filename = message.video.file_name
        user_peer_message.mimetype = message.video.mime_type
        user_peer_message.filepath = os.path.join(path, user_peer_message.filename)

    if message.video_note:
        user_peer_message.file_id = message.video_note.file_id
        user_peer_message.filename = get_filename(message.video_note.file_id, "video/mp4")
        user_peer_message.mimetype = "video/mp4"
        user_peer_message.filepath = os.path.join(path, user_peer_message.filename)

    if message.voice:
        user_peer_message.file_id = message.voice.file_id
        user_peer_message.filename = get_filename(message.voice.file_id, message.voice.mime_type)
        user_peer_message.mimetype = message.voice.mime_type
        user_peer_message.filepath = os.path.join(path, user_peer_message.filename)

    await bot.download(file=user_peer_message.file_id, destination=user_peer_message.filepath)

    return user_peer_message


def get_filename(
        file_id: str, mimetype: str
):
    if not (extension := MimeTypes().guess_extension(mimetype)):
        extension = "." + mimetype.split("/")[1]
    return file_id + extension


def create_input_media(user_peer_message: UserPeerMessage, text_pattern: str) -> Union[
    InputMediaAudio, InputMediaDocument, InputMediaPhoto, InputMediaVideo
]:
    text = text_pattern.format(text=user_peer_message.text)
    if user_peer_message.type == ContentType.AUDIO:
        return InputMediaAudio(
            media=FSInputFile(user_peer_message.filepath, user_peer_message.filename), caption=text
        )

    if user_peer_message.type == ContentType.DOCUMENT:
        return InputMediaDocument(
            media=FSInputFile(user_peer_message.filepath, user_peer_message.filename), caption=text
        )

    if user_peer_message.type == ContentType.PHOTO:
        return InputMediaPhoto(
            media=FSInputFile(user_peer_message.filepath, user_peer_message.filename), caption=text
        )

    if user_peer_message.type == ContentType.VIDEO:
        return InputMediaVideo(
            media=FSInputFile(user_peer_message.filepath, user_peer_message.filename), caption=text
        )


async def send_content_with_pattern(
        chat_id: int, user_peer_message: UserPeerMessage, text_pattern: str, markup: InlineKeyboardMarkup
):
    return await send_content(chat_id, user_peer_message, text_pattern.format(text=user_peer_message.text), markup)


async def send_content(
        chat_id: int, user_peer_message: UserPeerMessage, text: Optional[str], markup: InlineKeyboardMarkup
):
    if user_peer_message.type == ContentType.AUDIO:
        await bot.send_audio(
            chat_id=chat_id, audio=FSInputFile(user_peer_message.filepath, user_peer_message.filename),
            caption=text, reply_markup=markup
        )

    if user_peer_message.type == ContentType.DOCUMENT:
        await bot.send_document(
            chat_id=chat_id, document=FSInputFile(user_peer_message.filepath, user_peer_message.filename),
            caption=text, reply_markup=markup
        )

    if user_peer_message.type == ContentType.PHOTO:
        await bot.send_photo(
            chat_id=chat_id, photo=FSInputFile(user_peer_message.filepath),
            caption=text, reply_markup=markup
        )

    if user_peer_message.type == ContentType.VIDEO:
        await bot.send_video(
            chat_id=chat_id, video=FSInputFile(user_peer_message.filepath, user_peer_message.filename),
            caption=text, reply_markup=markup
        )

    if user_peer_message.type == ContentType.VIDEO_NOTE:
        await bot.send_video_note(
            chat_id=chat_id, video_note=FSInputFile(user_peer_message.filepath), reply_markup=markup
        )

    if user_peer_message.type == ContentType.VOICE:
        await bot.send_voice(
            chat_id=chat_id, voice=FSInputFile(user_peer_message.filepath),
            caption=text, reply_markup=markup
        )


async def send_message_edited(
        peer: Union[User, Chat], last_user_peer_message: UserPeerMessage, new_user_user_peer_message: UserPeerMessage
):
    markup = user_link_markup(peer)

    if last_user_peer_message:
        if last_user_peer_message.type == ContentType.TEXT and new_user_user_peer_message.type == ContentType.TEXT:
            await bot.send_message(
                chat_id=new_user_user_peer_message.user_id,
                text=EDIT_MESSAGE_TEXT.format(
                    last_user_peer_message_text=last_user_peer_message.text,
                    new_user_peer_message_text=new_user_user_peer_message.text
                ),
                reply_markup=markup
            )

        elif last_user_peer_message.type in MEDIA_GROUP_TYPES and new_user_user_peer_message.type in MEDIA_GROUP_TYPES:
            await bot.send_media_group(
                chat_id=new_user_user_peer_message.user_id,
                media=[
                    create_input_media(last_user_peer_message, BEFORE_EDIT_MESSAGE_TEXT),
                    create_input_media(new_user_user_peer_message, AFTER_EDIT_MESSAGE_TEXT)
                ]
            )
            await bot.send_message(
                chat_id=new_user_user_peer_message.user_id,
                text=EDIT_MESSAGE_TEXT.format(
                    last_user_peer_message_text=last_user_peer_message.text,
                    new_user_peer_message_text=new_user_user_peer_message.text
                ),
                reply_markup=markup
            )


        elif last_user_peer_message.type not in NOTE_TYPES and new_user_user_peer_message.type not in NOTE_TYPES:
            content_message = last_user_peer_message \
                if last_user_peer_message.type in MEDIA_TYPES else new_user_user_peer_message
            await send_content(
                last_user_peer_message.user_id, content_message, EDIT_MESSAGE_TEXT.format(
                    last_user_peer_message_text=last_user_peer_message.text,
                    new_user_peer_message_text=new_user_user_peer_message.text,
                    markup=markup
                )
            )

        else:
            if last_user_peer_message.type in MEDIA_TYPES:
                await send_content_with_pattern(
                    last_user_peer_message.user_id, last_user_peer_message, BEFORE_EDIT_MESSAGE_TEXT, markup
                )
            else:
                await bot.send_message(
                    chat_id=new_user_user_peer_message.user_id,
                    text=BEFORE_EDIT_MESSAGE_TEXT.format(text=last_user_peer_message.text),
                    reply_markup=markup
                )

            if new_user_user_peer_message.type in MEDIA_TYPES:
                await send_content_with_pattern(
                    new_user_user_peer_message.user_id, new_user_user_peer_message, AFTER_EDIT_MESSAGE_TEXT, markup
                )
            else:
                await bot.send_message(
                    chat_id=new_user_user_peer_message.user_id,
                    text=AFTER_EDIT_MESSAGE_TEXT.format(text=new_user_user_peer_message.text),
                    reply_markup=markup
                )

    else:
        await send_content_with_pattern(
            new_user_user_peer_message.user_id, new_user_user_peer_message, new_user_user_peer_message.text, markup
        )


async def send_message_deleted(peer: Union[User, Chat], user_peer_message: UserPeerMessage):
    markup = user_link_markup(peer)

    if user_peer_message.type == ContentType.VIDEO_NOTE:
        await bot.send_message(
            chat_id=user_peer_message.user_id,
            text=DELETE_VIDEO_NOTE_MESSAGE_TEXT
        )
        await send_content(
            user_peer_message.user_id, user_peer_message, None, markup
        )

    elif user_peer_message.type in MEDIA_TYPES:
        await send_content_with_pattern(
            user_peer_message.user_id, user_peer_message, DELETE_MESSAGE_TEXT, markup
        )

    else:
        await bot.send_message(
            chat_id=user_peer_message.user_id,
            text=DELETE_MESSAGE_TEXT.format(text=user_peer_message.text),
            reply_markup=markup
        )


async def send_protected_content(peer: Union[User, Chat], protected_peer_message: UserPeerMessage):
    await send_content(protected_peer_message.user_id, protected_peer_message, None, user_link_markup(peer))


async def cron_delete_messages():
    from_date = datetime.now() - timedelta(days=settings.DAYS_TO_SAVE_CONTENT)

    while True:
        logger.info(f"Start deleting messages from {from_date}")
        try:
            while messages := await user_peer_message_repository.get_messages_earlier_date(from_date=from_date):
                await user_peer_message_repository.delete(UserPeerMessage.id.in_([message.id for message in messages]))
                await storage.deleteAll([message.filepath for message in messages if message.filepath])
        except Exception as e:
            logger.error("Error to cron delete messages", e)
        await asyncio.sleep(settings.CRON_SECONDS_TO_DELETE_MESSAGES)

