import abc
import logging
import os
from typing import Iterable

import aiofiles
import aiofiles.os
from aiogram.types import BufferedInputFile

logger = logging.getLogger(__name__)


class Storage(abc.ABC):

    @abc.abstractmethod
    async def save(self, key: str, file: bytes) -> str:
        pass

    @abc.abstractmethod
    async def get(self, key: str) -> BufferedInputFile:
        pass

    @abc.abstractmethod
    async def delete(self, key: str):
        pass

    @abc.abstractmethod
    async def deleteAll(self, keys: Iterable[str]):
        pass


class FileSystemStorage(Storage):
    async def save(self, key: str, file: bytes) -> str:
        try:
            async with aiofiles.open(key, "wb") as handle:
                await handle.write(file)
            return key
        except Exception as e:
            logger.error(f"Error to save file {key}", e)

    async def get(self, key: str) -> BufferedInputFile:
        try:
            async with aiofiles.open(key, "rb") as handle:
                filename = os.path.basename(key)
            return BufferedInputFile(await handle.read(), filename)
        except Exception as e:
            logger.error(f"Error to get file {key}", e)

    async def delete(self, key: str):
        try:
            await aiofiles.os.remove(key)
        except Exception as e:
            logger.error(f"Error to delete file {key}", e)

    async def deleteAll(self, keys: Iterable[str]):
        for key in keys:
            await self.delete(key)
