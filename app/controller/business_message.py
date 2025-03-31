from aiogram import Router
from aiogram.types import Message, BusinessMessagesDeleted, ContentType

from app.database.models import UserPeerMessage
from app.loader import bot, user_peer_message_repository
from app.utils.content import message_has_content, create_content_dir, download_message_content

router = Router()


@router.business_message()
async def user_message(message: Message):
    business_connection = await bot.get_business_connection(message.business_connection_id)
    date = message.date.replace(tzinfo=None)

    path_to_files = None
    if message_has_content(message):
        path_to_files = create_content_dir(
            user_id=business_connection.user.id, chat_id=message.chat.id, message_id=message.message_id,
            date=int(date.timestamp())
        )
        await download_message_content(message, path_to_files)

    await user_peer_message_repository.create(
        UserPeerMessage(
            user_id=business_connection.user.id,
            chat_id=message.chat.id,
            message_id=message.message_id,
            message=message.model_dump_json(exclude_none=True),
            path_to_files=path_to_files,
            created_at=date,
            updated_at=date
        )
    )


@router.edited_business_message()
async def user_edited_message(message: Message):
    # message.edit_date
    print(type(message), message)


@router.deleted_business_messages()
async def user_delete_message(message: BusinessMessagesDeleted):
    print(type(message), message)
