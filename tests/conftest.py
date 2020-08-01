import logging
import os
from os import environ

import orjson
import pytest
from _testcapi import INT_MAX
from aiohttp.web import Request, Response
from aiohttp.web_response import json_response
from aresponses import ResponsesMockServer
from lsm import LSM
from socks5.server import Socks5

from manser.client.manga.mangahub import MangaHub
from manser.client.manga.mangalib import Mangalib
from manser.client.manga.readmanga import Readmanga
from manser.client.manga.remanga import Remanga
from manser.client.proxy6 import Proxy6
from manser.client.store import Store

environ["PROXY6_TOKEN"] = "test-key"
from manser.config import DBNAME, PROXY6_TOKEN, UPDATE_INTERVAL

log = logging.getLogger(__name__)


@pytest.fixture
def store():
    store = Store(LSM(DBNAME), UPDATE_INTERVAL)
    yield store
    store.db.close()
    os.remove(DBNAME)


@pytest.fixture
async def proxy6():
    client = Proxy6(PROXY6_TOKEN)
    await client.init()
    yield client
    await client.close()


@pytest.fixture
async def readmanga(store: Store, proxy6: Proxy6):
    client = Readmanga(store=store, proxy6=proxy6)
    yield client
    await client.close()


@pytest.fixture
async def mangalib(store: Store, proxy6: Proxy6):
    client = Mangalib(store=store, proxy6=proxy6)
    yield client
    await client.close()


@pytest.fixture
async def mangahub(store: Store, proxy6: Proxy6):
    client = MangaHub(store=store, proxy6=proxy6)
    yield client
    await client.close()


@pytest.fixture
async def remanga(store: Store, proxy6: Proxy6):
    client = Remanga(store=store, proxy6=proxy6)
    yield client
    await client.close()


@pytest.fixture
async def aresponses():
    async with ResponsesMockServer() as server:
        yield server


def json(name):
    def response(request: Request):
        path = request.path.replace("?", "").strip("/")
        with open(f"tests/json/{name}-{path}.json", "rb") as fp:
            return json_response(data=orjson.loads(fp.read()), status=200)

    return response


def html(name):
    def response(request: Request):
        log.info("Return html for %r", name)
        with open(f"tests/html/{name}-{request.path.strip('/')}.html", "rb") as fp:
            return Response(status=200, body=fp.read())

    return response


@pytest.fixture
async def socks5_server():
    server = Socks5(host="127.0.0.1", port=9440)
    await server.start_server()
    yield
    await server.stop_server()


@pytest.fixture(autouse=True)
async def sources(aresponses, socks5_server):
    aresponses.add("readmanga.live", method_pattern="GET", response=html("readmanga"))
    aresponses.add("mangahub.ru", method_pattern="GET", response=html("mangahub"))
    aresponses.add(
        "remanga.org", method_pattern="GET", response=json("remanga"), repeat=2
    )
    aresponses.add("mangalib.me", method_pattern="GET", response=html("mangalib"))
    aresponses.add(
        "proxy6.net", method_pattern="GET", response=json("proxy6"), repeat=INT_MAX
    )
