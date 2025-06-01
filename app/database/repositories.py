from collections.abc import Sequence
from datetime import datetime
from typing import Dict, Any, Tuple

from sqlalchemy import select, delete, func
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
    async def paginated_filter(
            self, *args: tuple[Any], session: AsyncSession, limit: int = 20, offset: int = 0, **kwargs: Dict[str, Any]
    ) -> Tuple[int, Sequence[BaseModel]]:
        """
        Возвращает общее количество записей и список моделей с учетом пагинации.
        """
        base_query = select(self.model).filter(*args).filter_by(**kwargs)
        count_query = select(func.count()).select_from(self.model).filter(*args).filter_by(**kwargs)

        total_result = await session.execute(count_query)
        total = total_result.scalar()

        paginated_query = base_query.limit(limit).offset(offset)
        result = await session.execute(paginated_query)
        items = result.scalars().all()

        return total, items

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

    @connection
    async def get_messages_earlier_date(
            self, session: AsyncSession, from_date: datetime.date, limit: int = 1000
    ) -> Sequence[BaseModel]:
        result = await session.execute(
            select(UserPeerMessage)
            .filter(UserPeerMessage.created_at <= from_date)
            .order_by(UserPeerMessage.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()
