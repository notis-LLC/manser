import logging
from contextlib import suppress
from datetime import datetime, timedelta
from enum import Enum, unique
from typing import Generator, List, Optional

import orjson
from lsm import LSM
from pydantic import BaseModel, HttpUrl

from manser.client.feedly import FeedlyItemsResponseModel

log = logging.getLogger(__name__)


class BaseLatestValidator(BaseModel):
    tome: int
    number: float
    name: str
    date: float
    href: HttpUrl

    class Config:
        # json_dumps = orjson.dumps
        json_loads = orjson.loads


class HistoryModel(BaseModel):
    url: HttpUrl
    title: str
    published: datetime
    crawled: datetime
    updated_at: datetime = datetime.now()
    slug: str

    @classmethod
    def from_feedly(cls, item: FeedlyItemsResponseModel):
        return cls(
            url=item.originId,
            title=item.title,
            published=item.published,
            crawled=item.crawled,
            slug=item.originId.path.split("/")[0],
        )


class MangaStoreModel(BaseModel):
    pass


class StoreFinish(Exception):
    pass


@unique
class SourceType(int, Enum):
    Readmanga = 1
    Mangahub = 2


class UserStore:
    db: LSM

    @property
    def _prefix(self):
        return "user"

    def _key(self, *args: str) -> str:
        return "-".join([self._prefix, *args])

    def update_user(self, uid: int, manga: str, type: SourceType):
        key = self._key(str(uid), manga, str(type.value))
        self.db[key] = orjson.dumps(dict(updated_at=datetime.now()))
        self.db.commit()

    def user(self, uid: int) -> List:
        result = []
        for key, value in self.db[self._key(str(uid), "-"):]:
            result.append(dict(key=key.decode(), value=value.decode()))
        return result


class MangaStore:
    db: LSM
    update_interval: timedelta

    def need_update(self, parser: str, slug: str) -> bool:
        try:
            key = self.db[f"update-{parser}-{slug}"].decode()
        except KeyError:
            return True

        dt = datetime.fromisoformat(key)
        log.info(
            "Need update: dt: %r, now: %r, update interval: %r",
            dt,
            datetime.utcnow(),
            self.update_interval,
        )
        return (datetime.utcnow() - dt) > self.update_interval

    def save(self, parser: str, slug: str, model: List[BaseLatestValidator]) -> None:
        for i, manga in enumerate(model):
            self.db[f"manga-{parser}-{slug}-{str(i).zfill(4)}"] = manga.json()
        self.db[f"update-{parser}-{slug}"] = datetime.utcnow()
        self.db.commit()

    def load(
            self, parser: str, slug: str, limit: int = 0, after: Optional[float] = None
    ) -> Generator[BaseLatestValidator, None, None]:
        key = f"manga-{parser}-{slug}-"
        for i, (key, val) in enumerate(self.db.fetch_range(key, key + str(9999))):
            if limit and i >= limit:
                return None
            data = BaseLatestValidator(**orjson.loads(val))
            with suppress(ValueError):
                if after is not None and data.date <= after:
                    return None
            yield data


class Store(UserStore, MangaStore):
    def __init__(self, db: LSM, update_interval: timedelta):
        self.db = db
        self.update_interval = update_interval
