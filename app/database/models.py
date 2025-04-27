from datetime import datetime

from aiogram.types import ContentType
from sqlalchemy import Integer, ForeignKey, BigInteger, JSON, VARCHAR, TEXT, Enum
from sqlalchemy import String
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, declared_attr
from sqlalchemy.orm import Mapped, mapped_column


# Базовый класс для всех моделей
class BaseModel(AsyncAttrs, DeclarativeBase):
    __abstract__ = True  # Класс абстрактный, чтобы не создавать отдельную таблицу для него

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    @declared_attr.directive
    def __tablename__(cls) -> str:
        return cls.__name__.lower() + "s"


class User(BaseModel):
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=True)
    full_name: Mapped[str] = mapped_column(String, nullable=False)


class UserPeerMessage(BaseModel):
    user_id: Mapped[int] = mapped_column(ForeignKey(f"{User.__tablename__}.id"), nullable=False)
    chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    message_id: Mapped[int] = mapped_column(BigInteger, nullable=False)

    type: Mapped[ContentType] = mapped_column(Enum(ContentType), nullable=False)
    message: Mapped[dict] = mapped_column(JSON, nullable=False)
    text: Mapped[str] = mapped_column(TEXT, nullable=True)

    file_id: Mapped[str] = mapped_column(VARCHAR(256), nullable=True)
    filepath: Mapped[str] = mapped_column(VARCHAR(256), nullable=True)
    filename: Mapped[str] = mapped_column(VARCHAR(256), nullable=True)
    mimetype: Mapped[str] = mapped_column(VARCHAR(128), nullable=True)
