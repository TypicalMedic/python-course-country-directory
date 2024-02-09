"""
Базовые функции сборщиков информации о странах.
"""
import logging
import time
from abc import ABC, abstractmethod
from typing import Iterable, Any, Optional

import aiofiles
import aiofiles.os


class BaseCollector(ABC):
    """
    Базовый класс, реализующий интерфейс для сборщиков информации.
    """

    @abstractmethod
    async def collect(self, **kwargs: Any) -> Optional[Iterable[Any]]:
        ...

    @staticmethod
    @abstractmethod
    async def get_file_path(**kwargs: Any) -> str:
        ...

    @staticmethod
    @abstractmethod
    async def get_cache_ttl() -> int:
        ...

    async def cache_invalid(self, **kwargs: Any) -> bool:
        """
        Проверка необходимости актуализации данных в кэше.
        Если True, то необходимо актуализировать данные в кэше, иначе брать данные из кэша.

        :return: bool
        """

        file_path = await self.get_file_path(**kwargs)
        logging.info(await self.get_cache_ttl())
        logging.info(time.time() - await aiofiles.os.path.getmtime(file_path))
        if (
            # проверка существования файла
            # (если файл не существует)
            not await aiofiles.os.path.isfile(file_path)
            # проверка наличия содержимого в файле без валидации структуры и значений
            # (или если файл существует, но он пустой)
            or not await aiofiles.os.path.getsize(file_path)
            # проверка срока актуальности кэша
            # путем сравнения разницы между текущим временем
            # и времени последнего изменения файла
            # (или если файл существует и не пустой, но данные в нем уже устарели)
            or (time.time() - await aiofiles.os.path.getmtime(file_path))
            > await self.get_cache_ttl()
        ):
            return True

        return False
