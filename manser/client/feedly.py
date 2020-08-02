from datetime import datetime
from typing import List, Optional

from aiohttp import ClientSession
from pydantic import BaseModel, HttpUrl
from yarl import URL


class FeedlyAlternateResponseModel(BaseModel):
    href: HttpUrl
    type: str


class FeedlyItemsSummaryResponseModel(BaseModel):
    content: str
    direction: str


class FeedlyItemsOriginResponseModel(BaseModel):
    streamId: str
    title: str
    htmlUrl: HttpUrl


class FeedlyItemsResponseModel(BaseModel):
    id: str
    originId: HttpUrl
    fingerprint: str
    title: str
    alternate: List[FeedlyAlternateResponseModel]
    crawled: datetime
    published: datetime
    origin: FeedlyItemsOriginResponseModel
    unread: bool


class FeedlyResponseModel(BaseModel):
    id: str
    title: str
    updated: datetime
    continuation: str = None
    alternate: List[FeedlyAlternateResponseModel]
    items: List[FeedlyItemsResponseModel]


class FeedlyClient:
    def __init__(self):
        self.base = URL("https://cloud.feedly.com/v3/streams/contents")
        self.conn = ClientSession()

    async def close(self):
        await self.conn.close()

    async def mangas(
        self, count: int, continuation: Optional[str]
    ) -> FeedlyResponseModel:
        url = self.base.with_query(
            streamId="feed/http://feeds.feedburner.com/readmangarss", count=count
        )
        if continuation:
            url = url.update_query(continuation=continuation)

        result = await self.conn.get(url)
        return FeedlyResponseModel(**await result.json())
