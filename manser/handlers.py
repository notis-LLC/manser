from types import MappingProxyType
from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, Response
from lsm import LSM
from more_itertools import take
from pydantic import BaseModel
from yarl import URL

from manser.client.manga.abc import BaseLatestValidator, BaseMangaSource
from manser.client.manga.mangahub import MangaHub
from manser.client.manga.mangalib import Mangalib
from manser.client.manga.readmanga import Readmanga
from manser.client.manga.remanga import Remanga
from manser.client.proxy6 import Proxy6
from manser.client.store import Store
from manser.config import DBNAME, PROXY6_TOKEN, UPDATE_INTERVAL

router = APIRouter()


def store():
    return Store(LSM(DBNAME), UPDATE_INTERVAL)


def proxy6():
    return Proxy6(PROXY6_TOKEN)


async def readmanga(store=Depends(store), proxy6=Depends(proxy6)):
    connector = await proxy6.connector()
    client = Readmanga(store, connector=connector)
    yield client
    await client.close()


async def mangahub(store=Depends(store), proxy6=Depends(proxy6)):
    connector = await proxy6.connector()
    client = MangaHub(store, connector=connector)
    yield client
    await client.close()


async def remanga(store=Depends(store), proxy6=Depends(proxy6)):
    connector = await proxy6.connector()
    client = Remanga(store, connector=connector)
    yield client
    await client.close()


async def mangalib(store=Depends(store), proxy6=Depends(proxy6)):
    connector = await proxy6.connector()
    client = Mangalib(store, connector=connector)
    yield client
    await client.close()


def mapping(
    readmanga=Depends(readmanga),
    mangahub=Depends(mangahub),
    remanga=Depends(remanga),
    mangalib=Depends(mangalib),
):
    return MappingProxyType(
        {
            "readmanga.me": readmanga,
            "readmanga": readmanga,
            "mangahub.ru": mangahub,
            "mangahub": mangahub,
            "remanga.org": remanga,
            "remanga": remanga,
            "mangalib.me": mangalib,
            "mangalib": mangalib,
        }
    )


class ResultManga(BaseModel):
    mangas: List[BaseLatestValidator]
    total: int


async def update_cache(parser: BaseMangaSource, slug: str):
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
    mangas = take(limit, parser.load(slug))
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
