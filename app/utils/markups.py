from sys import prefix

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, User, Chat

from app.loader import bot
from app.utils.constants import ChatAction, chat_action_names


def user_link_markup(user: User) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="👤 " + user.full_name, url=f"tg://user?id={user.id}")
            ]
        ]
    )
