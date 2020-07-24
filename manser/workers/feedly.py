import logging
from asyncio import sleep
from datetime import timedelta

from manser.client.feedly import FeedlyClient
from manser.client.manga.readmanga import Readmanga

log = logging.getLogger(__name__)


async def readmanga_feedly_updater(
    feedly: FeedlyClient, readmanga: Readmanga, count: int = 10
):
    log.info("Init readmanga feedly")
    while True:
        try:
            await readmanga.feedly_worker(feedly, count)
            await sleep(timedelta(minutes=10).total_seconds())
        except Exception:
            log.exception("Failed in filler")
            continue
