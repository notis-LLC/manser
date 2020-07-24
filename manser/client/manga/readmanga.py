import logging
import re
from datetime import datetime
from typing import AsyncGenerator, Optional

from lxml.cssselect import CSSSelector
from lxml.html import fromstring
from yarl import URL

from manser.client.feedly import FeedlyClient
from manser.client.manga.abc import BaseLatestValidator, BaseMangaSource, ParsingError
from manser.client.store import HistoryModel, Store

log = logging.getLogger(__name__)


class Readmanga(BaseMangaSource):
    def __init__(self, store: Store, **kwargs):
        self.regex = r"(.*?)(\d+)\s\-?\s?(\d+)?(.*)"
        self.parser = "readmanga"
        super().__init__(
            url=URL("https://readmanga.live"), store=store, key=self.parser, **kwargs
        )

    def parse(self, date: datetime, title: str, href: str) -> BaseLatestValidator:
        found = re.match(self.regex, title)
        if not found:
            log.warning("Failed to find in title, for %r", self.key)
            raise ParsingError

        _ = found.group(1)
        tome = int(found.group(2))
        try:
            number = float(found.group(3))
        except (AttributeError, TypeError):
            number = tome
            tome = 0

        try:
            name = found.group(4).strip()
        except AttributeError:
            name = ""
        return BaseLatestValidator(
            date=date, tome=tome, number=number, name=name, href=href
        )

    async def latest(self, slug: str) -> AsyncGenerator[BaseLatestValidator, None]:
        body = await self.request(slug)
        css = CSSSelector(".chapters-link > .table > tr")
        html = fromstring(body.decode())
        elements = [e.cssselect("td") for e in css(html)]
        chapters = list(filter(lambda x: len(x) == 2, elements))
        for chapter in chapters:
            raw_date = chapter[1].text.replace("\n", "").strip()
            date = datetime.strptime(raw_date, "%d.%m.%y")
            text = chapter[0].find("a").text.replace("\n", "").replace("\r", "")
            path = chapter[0].find("a").attrib["href"].lstrip("/")
            yield self.parse(date, text, str(self.url / path))

    async def feedly_worker(
        self, feedly: FeedlyClient, count: int, continuation: Optional[str] = None
    ):
        mangas = await feedly.mangas(count, continuation)
        for manga in mangas.items:
            model = HistoryModel.from_feedly(manga)

            try:
                manga, tome, number, name = self.parse(
                    model.updated_at, model.title, model.url
                )
            except Exception:
                print("FAIL: --", manga.title, "--", model.url, manga.json())
                log.warning("fail")
                continue

            # self.store.save_readmanga(model)

        print("Commit: ", mangas.items[0].originId)
        return mangas.continuation
