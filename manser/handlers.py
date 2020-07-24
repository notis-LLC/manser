import logging
import time
from types import MappingProxyType
from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, Request, Response
from more_itertools import take
from pydantic import BaseModel
from yarl import URL

from manser.client.manga.abc import BaseLatestValidator, BaseMangaSource

log = logging.getLogger(__name__)

router = APIRouter()


def mapping(request: Request):
    log.info("Create deps mapping")
    state = request.app.state
    return MappingProxyType(
        {
            "readmanga.me": state.readmanga,
            "readmanga.live": state.readmanga,
            "readmanga": state.readmanga,
            "mangahub.ru": state.mangahub,
            "mangahub": state.mangahub,
            "remanga.org": state.remanga,
            "remanga": state.remanga,
            "mangalib.me": state.mangalib,
            "mangalib": state.mangalib,
        }
    )


class ResultManga(BaseModel):
    mangas: List[BaseLatestValidator]
    total: int


async def update_cache(parser: BaseMangaSource, slug: str):
    log.info("Update cache for %r, manga: %r", parser.key, slug)
    await parser.save(slug)


@router.get("/manga/{source}/chapters/{slug}", response_model=ResultManga)
async def manga(
    background_tasks: BackgroundTasks,
    source: str,
    slug: str,
    limit: int = 20,
    mapping: MappingProxyType = Depends(mapping),
):
    parser = mapping[source]
    t = time.monotonic()
    mangas = take(limit, parser.load(slug))
    log.info("time: %r", time.monotonic() - t)
    background_tasks.add_task(update_cache, parser, slug)
    return ResultManga(mangas=mangas, total=0)


@router.get(
    "/manga/byUrl/{raw_url:path}",
    response_model=ResultManga,
    responses={204: dict(description="Cannot find matched url")},
)
async def byurl(
    raw_url: str, limit: int = 20, mapping: MappingProxyType = Depends(mapping)
):
    url = URL(raw_url)
    try:
        process = mapping[url.host]
        slug = url.path.lstrip("/")
        mangas = take(limit, process.load(slug))
        return ResultManga(mangas=mangas, total=0)
    except KeyError:
        return Response(status_code=204)
