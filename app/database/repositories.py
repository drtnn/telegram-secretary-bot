from collections.abc import Sequence
from typing import Dict, Any

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import BaseModel, User, UserPeerMessage
from app.database.session import connection


class BaseRepository:
    model: BaseModel.__class__

    @connection
    async def create(
            self, instance: BaseModel, session: AsyncSession
    ) -> BaseModel:
        session.add(instance)
        await session.commit()
        return instance

    @connection
    async def get_or_none(self, *args: tuple[Any], session: AsyncSession, **kwargs: Dict[str, Any]) -> BaseModel:
        result = await session.execute(select(self.model).filter(*args).filter_by(**kwargs))
        return result.scalar_one_or_none()

    @connection
    async def get_or_create(
            self, instance: BaseModel, session: AsyncSession,
            filter_args: tuple[Any] = None, filter_kwargs: Dict[str, Any] = None
    ) -> BaseModel:
        if not filter_args:
            filter_args = ()
        if not filter_kwargs:
            filter_kwargs = {}

        if db_instance := await self.get_or_none(session=session, *filter_args, **filter_kwargs):
            return db_instance
        else:
            return await self.create(session=session, instance=instance)

    @connection
    async def filter(self, *args: tuple[Any], session: AsyncSession, **kwargs: Dict[str, Any]) -> Sequence[BaseModel]:
        result = await session.execute(select(self.model).filter(*args).filter_by(**kwargs))
        return result.scalars().all()

    @connection
    async def delete(self, *args: tuple[Any], session: AsyncSession, **kwargs: Dict[str, Any]):
        await session.execute(delete(self.model).filter(*args).filter_by(**kwargs))
        await session.commit()


class UserRepository(BaseRepository):
    model = User


class UserPeerMessageRepository(BaseRepository):
    model = UserPeerMessage

    @connection
    async def get_last_message(
            self, user_id: int, chat_id: int, message_id: int, session: AsyncSession
    ) -> BaseModel:
        result = await session.execute(
            select(UserPeerMessage)
            .filter_by(user_id=user_id, chat_id=chat_id, message_id=message_id)
            .order_by(UserPeerMessage.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
