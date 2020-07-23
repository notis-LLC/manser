import re
from datetime import datetime
from typing import AsyncGenerator

import orjson
from lxml.cssselect import CSSSelector
from lxml.html import fromstring
from yarl import URL

from manser.client.manga.abc import BaseLatestValidator, BaseMangaSource
from manser.client.store import Store


class Mangalib(BaseMangaSource):
    def __init__(self, store: Store, **kwargs):
        self.regex = r".*Том +(\d+)\. Глава (\d+).*"

        super().__init__(
            url=URL("https://mangalib.me"), store=store, key="mangalib", **kwargs
        )

    def parse(self, slug: str, e) -> BaseLatestValidator:
        try:
            link = e.cssselect("a")[0]
            path = link.attrib["href"]
            text = self.strip_text(link.text)
            name = link.attrib["title"]
        except IndexError:
            teams = (orjson.loads(e.attrib["data-teams"]))[-1]["slug"]
            link = (
                self.url
                / slug
                / f"v{e.attrib['data-volume']}"
                / f"c{e.attrib['data-number']}"
                / teams
            )
            path = str(link)
            text = self.strip_text(
                e.cssselect("div.chapter-item__name")[0].text_content()
            )
            name_span = [
                s.text.lstrip("- ")
                for s in e.cssselect("span")
                if s.text and s.text.startswith("- ")
            ]
            name = name_span[0] if name_span else ""

        found = re.match(self.regex, text)
        tome = int(found.group(1))
        number = float(found.group(2))

        raw_date = self.normalize_date(e.cssselect(".chapter-item__date")[0].text)
        date = datetime.strptime(raw_date, "%d.%m.%Y")
        return BaseLatestValidator(
            name=name, tome=tome, number=number, date=date, href=path
        )

    async def latest(self, slug: str) -> AsyncGenerator[BaseLatestValidator, None]:
        body = await self.request(slug)
        css = CSSSelector(".chapter-item")
        html = fromstring(body.decode())

        for e in css(html):
            yield self.parse(slug, e)
