import asyncio
import logging
from asyncio import gather
from types import MappingProxyType

from fastapi import FastAPI
from lsm import LSM
from starlette_exporter import PrometheusMiddleware, handle_metrics

from manser.client.feedly import FeedlyClient
from manser.client.manga.mangahub import MangaHub
from manser.client.manga.mangalib import Mangalib
from manser.client.manga.readmanga import Readmanga
from manser.client.manga.remanga import Remanga
from manser.client.proxy6 import Proxy6
from manser.client.store import Store
from manser.config import (
    DBNAME,
    DEBUG,
    HOST,
    LOG_LEVEL,
    PORT,
    PROXY6_TOKEN,
    UPDATE_INTERVAL,
    WORKERS,
)
from manser.handlers import router
from manser.workers.feedly import readmanga_feedly_updater

log = logging.getLogger(__name__)

logging.basicConfig(
    format="[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s", level=LOG_LEVEL
)


def get_application() -> FastAPI:
    app = FastAPI(title="Manser - Ru manga updates API", debug=DEBUG)

    app.include_router(router)

    app.add_middleware(PrometheusMiddleware, app_name="manser")
    app.add_route("/metrics", handle_metrics)

    @app.on_event("startup")
    async def up():
        app.state.store = Store(LSM(DBNAME), UPDATE_INTERVAL)
        app.state.proxy6 = Proxy6(PROXY6_TOKEN)
        await app.state.proxy6.init()

        log.info("Create deps readmanga")
        app.state.readmanga = Readmanga(app.state.store, proxy6=app.state.proxy6)

        log.info("Create deps feedly")
        app.state.feedly = FeedlyClient()

        log.info("Create task readmanga updater")
        app.state.task_feedly_updater = asyncio.create_task(
            readmanga_feedly_updater(app.state.feedly, app.state.readmanga)
        )

        log.info("Create deps remanga")
        app.state.mangahub = MangaHub(app.state.store, proxy6=app.state.proxy6)

        log.info("Create deps remanga")
        app.state.remanga = Remanga(app.state.store, proxy6=app.state.proxy6)

        log.info("Create deps mangalib")
        app.state.mangalib = Mangalib(app.state.store, proxy6=app.state.proxy6)

        app.state.mapping = MappingProxyType(
            {
                "readmanga.me": app.state.readmanga,
                "readmanga.live": app.state.readmanga,
                "readmanga": app.state.readmanga,
                "mangahub.ru": app.state.mangahub,
                "mangahub": app.state.mangahub,
                "remanga.org": app.state.remanga,
                "remanga": app.state.remanga,
                "mangalib.me": app.state.mangalib,
                "mangalib": app.state.mangalib,
            }
        )

    @app.on_event("shutdown")
    async def down():
        app.state.task_feedly_updater.cancel()
        await gather(
            app.state.feedly.close(),
            app.state.readmanga.close(),
            app.state.mangahub.close(),
            app.state.remanga.close(),
            app.state.mangalib.close(),
        )
        app.state.store.db.close()
        await app.state.proxy6.close()

    return app


app = get_application()
