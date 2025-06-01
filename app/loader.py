from aiogram import Dispatcher, Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.config import settings
from app.database.repositories import UserRepository, UserPeerMessageRepository
from app.utils.storage import Storage, FileSystemStorage

bot = Bot(token=settings.TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

storage: Storage = FileSystemStorage()

user_repository = UserRepository()
user_peer_message_repository = UserPeerMessageRepository()
