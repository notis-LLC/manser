from datetime import datetime
from enum import Enum, unique
from typing import Generator, List, Optional

import orjson
from lsm import LSM
from pydantic import BaseModel, HttpUrl

from manser.client.feedly import FeedlyItemsResponseModel


class BaseLatestValidator(BaseModel):
    tome: int
    number: float
    name: str
    date: datetime
    href: HttpUrl

    # class Config:
    #     json_dumps = orjson.dumps


class HistoryModel(BaseModel):
    url: HttpUrl
    title: str
    published: datetime
    crawled: datetime
    updated_at: datetime = datetime.now()

    @classmethod
    def from_feedly(cls, item: FeedlyItemsResponseModel):
        return cls(
            url=item.originId,
            title=item.title,
            published=item.published,
            crawled=item.crawled,
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
        for key, value in self.db[self._key(str(uid), "-") :]:
            result.append(dict(key=key.decode(), value=value.decode()))
        return result


class MangaStore:
    db: LSM

    def save(self, parser: str, slug, model: List[BaseLatestValidator]) -> None:
        for i, manga in enumerate(model):
            self.db[f"manga-{parser}-{slug}-{str(i).zfill(4)}"] = manga.json()
        self.db[f"update-{parser}-{slug}"] = datetime.utcnow()
        self.db.commit()

    def load(
        self, parser: str, slug: str
    ) -> Generator[BaseLatestValidator, None, None]:
        key = f"manga-{parser}-{slug}-"
        for key, val in self.db.fetch_range(key, key + str(9999)):
            yield BaseLatestValidator(**orjson.loads(val))


class ReadmangaStore:
    db: LSM

    @property
    def cont(self):
        if self.db["readmanga-finish"]:
            raise StoreFinish
        try:
            return self.db["cont"].decode()
        except KeyError:
            return None

    def update_cont(self, value: Optional[str]):
        print("update", value)
        if not value:
            self.db["readmanga-finish"] = True
            return
        self.db["cont"] = value
        self.db["readmnga-cont"] = value
        self.db.commit()

    def save_readmanga(self, model: HistoryModel):
        self.db[f"history-readmanga-{model.url}"] = model.json()

    def get_readmanga(self, name: str) -> List[HistoryModel]:
        k = f"{name}/"
        result = []
        for key, val in self.db[f"history-readmanga-https://readmanga.me/{k}/":]:
            if k not in key.decode():
                break
            result.append(HistoryModel(**orjson.loads(val)))
        return result


class Store(UserStore, ReadmangaStore, MangaStore):
    def __init__(self, db: LSM):
        self.db = db
