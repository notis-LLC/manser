import pytest
from async_asgi_testclient import TestClient

from manser.__main__ import app
from manser.client.manga.abc import BaseMangaSource
from manser.client.store import Store

pytestmark = pytest.mark.asyncio


@pytest.fixture
def save(store: Store):
    async def inner(source: BaseMangaSource, slug: str):
        await source.save(slug)

    return inner


@pytest.fixture
async def asyncasgitestclient():
    yield TestClient(app)


@pytest.fixture
async def client(asyncasgitestclient):
    async with asyncasgitestclient:
        yield asyncasgitestclient


@pytest.mark.parametrize(
    "slug, exp",
    [
        (
            "van_pis",
            {
                "date": 1592611200.0,
                "href": "https://readmanga.live/van_pis/vol97/983",
                "name": "Раскат грома",
                "number": 983.0,
                "tome": 97,
            },
        ),
        (
            "cheshire_crossing",
            {
                "date": 1591920000.0,
                "href": "https://readmanga.live/cheshire_crossing/vol1/17",
                "name": "Птичка потеряла свои крылья",
                "number": 17.0,
                "tome": 1,
            },
        ),
    ],
)
async def test_readmanga(client, save, readmanga, slug, exp):
    await save(readmanga, slug)

    response = await client.get(f"/manga/readmanga/chapters/{slug}?limit=1")

    assert response.status_code == 200
    assert response.json() == {
        "mangas": [exp],
        "total": 0,
    }


@pytest.mark.parametrize(
    "slug, exp",
    [
        (
            "naruto",
            {
                "date": 1479513600.0,
                "href": "https://mangahub.ru/naruto/read/valik_prodzhekt/vol72/700/1/",
                "name": "Узумаки Наруто",
                "number": 700.0,
                "tome": 72,
            },
        ),
        (
            "cheshire_crossing",
            {
                "date": 1570924800.0,
                "href": "https://mangahub.ru/cheshire_crossing/read/wimer/vol1/10/1/",
                "name": "Лучше дома места нет",
                "number": 10.0,
                "tome": 1,
            },
        ),
    ],
)
async def test_mangahub(save, client, slug, exp, mangahub):
    await save(mangahub, slug)
    response = await client.get(f"/manga/mangahub/chapters/{slug}?limit=1")
    assert response.status_code == 200
    assert response.json() == {
        "mangas": [exp],
        "total": 0,
    }


@pytest.mark.parametrize(
    "slug, exp",
    [
        (
            "blade_of_demon_destruction",
            {
                "date": 1592288007.507449,
                "href": "https://remanga.org/manga/blade_of_demon_destruction/ch348061",
                "name": "КОНЕЦ",
                "number": 205.0,
                "tome": 24,
            },
        ),
        (
            "cheshire_crossing",
            {
                "date": 1592028602.607879,
                "href": "https://remanga.org/manga/cheshire_crossing/ch345901",
                "name": "Птичка потеряла свои крылья",
                "number": 17.0,
                "tome": 1,
            },
        ),
    ],
)
async def test_remanga(save, slug, exp, client, remanga):
    await save(remanga, slug)
    response = await client.get(f"/manga/remanga/chapters/{slug}?limit=1")
    assert response.status_code == 200
    assert response.json() == {
        "mangas": [exp],
        "total": 0,
    }


@pytest.mark.parametrize(
    "slug, exp",
    [
        (
            "yakusoku-no-neverland",
            {
                "date": 1592179200.0,
                "href": "https://mangalib.me/yakusoku-no-neverland/v17/c181/risens-team",
                "name": "Превозмогая судьбу",
                "number": 181.0,
                "tome": 17,
            },
        ),
        (
            "cheshire_crossing",
            {
                "date": 1591833600.0,
                "href": "https://mangalib.me/cheshire-crossing/v1/c17/wimer",
                "name": "Птичка потеряла свои крылья",
                "number": 17.0,
                "tome": 1,
            },
        ),
    ],
)
async def test_mangalib(save, client, slug, exp, mangalib):
    await save(mangalib, slug)
    response = await client.get(f"/manga/mangalib/chapters/{slug}?limit=1")
    assert response.status_code == 200
    assert response.json() == {
        "mangas": [exp],
        "total": 0,
    }


async def test_by_url(save, client, readmanga):
    await save(readmanga, "van_pis")
    response = await client.get("/manga/byUrl/https://readmanga.me/van_pis?limit=1")
    assert response.status_code == 200
    assert response.json() == {
        "mangas": [
            {
                "date": 1592611200.0,
                "href": "https://readmanga.live/van_pis/vol97/983",
                "name": "Раскат грома",
                "number": 983.0,
                "tome": 97,
            }
        ],
        "total": 0,
    }
