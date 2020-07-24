import logging
from asyncio import sleep
from datetime import timedelta

from filelock import FileLock

from manser.client.feedly import FeedlyClient
from manser.client.manga.readmanga import Readmanga

log = logging.getLogger(__name__)

lock = FileLock("manser.feedly.lock")


async def readmanga_feedly_updater(
    feedly: FeedlyClient, readmanga: Readmanga, count: int = 10
):
    lock.acquire(poll_intervall=1)
    try:
        log.info("Init readmanga feedly")
        while True:
            try:
                await readmanga.feedly_worker(feedly, count)
                await sleep(timedelta(minutes=10).total_seconds())
            except Exception:
                log.exception("Failed in filler")
                continue
    finally:
        lock.release()
