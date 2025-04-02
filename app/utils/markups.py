from typing import Union

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, User, Chat


def user_link_markup(user: Union[User, Chat]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="👤 " + user.full_name, url=f"tg://user?id={user.id}")
            ]
        ]
    )
