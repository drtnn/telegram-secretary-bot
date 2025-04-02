from aiogram import F, Router
from aiogram.enums import ChatType
from aiogram.types import BusinessMessagesDeleted, Message

from app.database.models import User
from app.loader import bot, user_peer_message_repository, user_repository
from app.utils.content import save_message, send_message_edited, send_message_deleted

router = Router()
router.business_message.filter(F.chat.type == ChatType.PRIVATE)


@router.business_message()
async def user_send_message(message: Message):
    await user_repository.get_or_create(
        User(id=message.from_user.id, username=message.from_user.username, full_name=message.from_user.full_name),
        filter_kwargs={"id": message.from_user.id}
    )

    business_connection = await bot.get_business_connection(message.business_connection_id)
    await save_message(message, business_connection)


@router.edited_business_message()
async def user_edited_message(message: Message):
    peer = await user_repository.get_or_create(
        User(id=message.from_user.id, username=message.from_user.username, full_name=message.from_user.full_name),
        filter_kwargs={"id": message.from_user.id}
    )

    business_connection = await bot.get_business_connection(message.business_connection_id)
    last_user_peer_message = await user_peer_message_repository.get_last_message(
        user_id=business_connection.user.id, chat_id=message.chat.id, message_id=message.message_id
    )
    new_user_peer_message = await save_message(message, business_connection)

    await send_message_edited(peer, last_user_peer_message, new_user_peer_message)


@router.deleted_business_messages()
async def user_delete_message(message: BusinessMessagesDeleted):
    peer = await user_repository.get_or_create(
        User(id=message.chat.id, username=message.chat.username, full_name=message.chat.full_name),
        filter_kwargs={"id": message.chat.id}
    )

    business_connection = await bot.get_business_connection(message.business_connection_id)
    for message_id in message.message_ids:
        last_user_peer_message = await user_peer_message_repository.get_last_message(
            user_id=business_connection.user.id, chat_id=message.chat.id, message_id=message_id
        )

        if last_user_peer_message:
            await send_message_deleted(peer, last_user_peer_message)
