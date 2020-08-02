import re
from datetime import datetime
from typing import AsyncGenerator, Tuple

from lxml.cssselect import CSSSelector
from lxml.html import fromstring
from yarl import URL

from manser.client.manga.abc import BaseLatestValidator, BaseMangaSource
from manser.client.store import Store


class MangaHub(BaseMangaSource):
    def __init__(self, store: Store, **kwargs):
        self.regex = r".*Том (\d+).\s+Глава\s([\d.]+)(.\s+\-\s(.*)'?)?"
        self.key = "mangahub"
        super().__init__(
            url=URL("https://mangahub.ru"), store=store, key=self.key, **kwargs
        )

    def parse(self, title: str) -> Tuple[int, float, str]:
        found = re.match(self.regex, title)
        tome = int(found.group(1))
        number = float(found.group(2))
        name = found.group(4) or ""
        return tome, number, name

    async def latest(self, slug: str) -> AsyncGenerator[BaseLatestValidator, None]:
        body = await self.request(slug)
        css = CSSSelector("div.px-3")
        html = fromstring(body.decode())

        for e in css(html):
            href = e.cssselect("a")[0].attrib["href"].lstrip("/")
            title = e.cssselect("a")[0].text.replace("\n", "").strip()
            tome, number, name = self.parse(title)
            raw_date = self.normalize_date(
                e.cssselect("div.ml-2.text-muted.text-nowrap")[0].text_content()
            )
            date = datetime.strptime(raw_date, "%d.%m.%Y")

            yield BaseLatestValidator(
                tome=tome,
                number=number,
                name=name,
                date=date.timestamp(),
                href=str(self.url / href),
            )
