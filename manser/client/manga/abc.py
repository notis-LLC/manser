import abc
from typing import AsyncGenerator, Generator, List

import orjson
from aiohttp import ClientSession, TCPConnector
from aioitertools import list
from yarl import URL

from manser.client.store import BaseLatestValidator, Store


class BaseMangaSource:
    def __init__(self, url: URL, connector: TCPConnector, store: Store, key: str):
        self.url = url
        self.session = ClientSession(connector=connector)
        self.store = store
        self.key = key

    async def close(self):
        await self.session.close()

    async def request(self, slug):
        res = await self.session.get(self.url / slug)
        return await res.read()

    async def json(self, slug: str):
        res = await self.session.get(self.url / slug)
        return await res.json(loads=orjson.loads)

    def normalize_date(self, text):
        return self.strip_text(text).replace(" ", "")

    def strip_text(self, text: str):
        return text.replace("\r", "").replace("\n", "")

    async def save(self, slug: str) -> None:
        if not self.store.need_update(self.key, slug):
            return None

        latest: List[BaseLatestValidator] = await list(self.latest(slug))
        self.store.save(self.key, slug, latest)
        return None

    @abc.abstractmethod
    async def latest(self, slug: str) -> AsyncGenerator[BaseLatestValidator, None]:
        raise NotImplementedError

    def load(self, slug: str) -> Generator[BaseLatestValidator, None, None]:
        yield from self.store.load(self.key, slug)
