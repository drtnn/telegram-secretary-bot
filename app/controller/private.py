from aiogram import F, Router
from aiogram.enums import ChatType
from aiogram.filters.command import CommandStart
from aiogram.types import Message

from app.database.models import User
from app.loader import user_repository
from app.utils.patterns import START_MESSAGE_PATTERN

router = Router()
router.my_chat_member.filter(F.chat.type == ChatType.PRIVATE)


@router.message(CommandStart())
async def user_start_command(message: Message):
    await user_repository.get_or_create(
        User(id=message.from_user.id, username=message.from_user.username, full_name=message.from_user.full_name),
        filter_kwargs={"id": message.from_user.id}
    )
    await message.answer(START_MESSAGE_PATTERN)
