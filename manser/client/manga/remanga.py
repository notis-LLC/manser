from datetime import datetime
from typing import AsyncGenerator, Dict, List, Callable

import pytz
from pydantic import BaseModel
from yarl import URL

from manser.client.manga.abc import BaseLatestValidator, BaseMangaSource
from manser.client.store import Store


class RemangaChapterValidator(BaseModel):
    id: int
    tome: int
    chapter: str
    name: str
    upload_date: datetime

    def to_base(self, url: URL, parse_time: Callable) -> BaseLatestValidator:
        return BaseLatestValidator(
            tome=self.tome,
            number=float(self.chapter),
            date=parse_time(self.upload_date),
            name=self.name,
            href=str(url / f"ch{self.id}"),
        )


class RemangaBranchValidator(BaseModel):
    id: int
    img: str
    total_votes: int
    count_chapters: int


class RemangaContentTitleValidator(BaseModel):
    id: int
    img: Dict[str, str]
    rus_name: str
    en_name: str
    another_name: str
    description: str
    branches: List[RemangaBranchValidator]
    active_branch: int = 0
    count_chapters: int = 0


class RemangaTitleValidator(BaseModel):
    content: RemangaContentTitleValidator


class RemangaChaptersValidator(BaseModel):
    content: List[RemangaChapterValidator]


class Remanga(BaseMangaSource):
    def __init__(self, store: Store, **kwargs):
        self.chapter_url = URL("https://remanga.org/manga")
        super().__init__(
            url=URL("https://api.remanga.org/api/titles"),
            store=store,
            key="remanga",
            **kwargs,
        )

    def normalize_slug(self, slug: str):
        return slug.lstrip("/manga/")

    async def latest(self, slug: str) -> AsyncGenerator[BaseLatestValidator, None]:
        title = RemangaTitleValidator(**await self.json(slug))
        for branch in title.content.branches:
            chapters = RemangaChaptersValidator(
                **await self.json("chapters/", dict(branch_id=branch.id))
            )
            for chapter in chapters.content:
                yield chapter.to_base(self.chapter_url / slug, self.unixtime)
