import logging
import time
from datetime import datetime
from typing import List

from fastapi import APIRouter, BackgroundTasks, Request, Response
from fastapi.responses import ORJSONResponse
from pydantic import BaseModel
from yarl import URL

from manser.client.manga.abc import BaseLatestValidator, BaseMangaSource

log = logging.getLogger(__name__)

router = APIRouter()


class ResultManga(BaseModel):
    mangas: List[BaseLatestValidator]
    total: int


async def update_cache(parser: BaseMangaSource, slug: str):
    log.info("Update cache for %r, manga: %r", parser.key, slug)
    await parser.save(slug)


@router.get(
    "/manga/{source}/chapters/{slug}",
    response_model=ResultManga,
    response_class=ORJSONResponse,
)
async def manga(
    background_tasks: BackgroundTasks,
    request: Request,
    source: str,
    slug: str,
    limit: int = 20,
    after: datetime = None,
):
    parser = request.app.state.mapping[source]
    mangas = parser.load(slug, limit, after)
    background_tasks.add_task(update_cache, parser, slug)
    return ResultManga(mangas=mangas, total=0)


@router.get(
    "/manga/byUrl/{raw_url:path}",
    response_model=ResultManga,
    responses={204: dict(description="Cannot find matched url")},
    response_class=ORJSONResponse,
)
async def byurl(
    background_tasks: BackgroundTasks,
    request: Request,
    raw_url: str,
    limit: int = 20,
    after: datetime = None,
):
    url = URL(raw_url)
    try:
        parser = request.app.state.mapping[url.host]
        slug = parser.normalize_slug(url.path)
        mangas = parser.load(slug, limit, after)
        background_tasks.add_task(update_cache, parser, slug)
        return ResultManga(mangas=mangas, total=0)
    except KeyError:
        return Response(status_code=204)
