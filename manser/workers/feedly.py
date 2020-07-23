import logging
from asyncio import sleep
from datetime import timedelta

from lsm import LSM

from manser.client.feedly import FeedlyClient
from manser.client.manga.readmanga import Readmanga
from manser.client.store import Store, StoreFinish

log = logging.getLogger(__name__)


async def history_filler(store: Store, count: int = 1000):
    rd = Readmanga(store)
    feedly = FeedlyClient()

    while True:
        try:
            cont = await rd.feedly_worker(feedly, count, store.cont)
            store.update_cont(cont)
            await sleep(10)
        except StoreFinish:
            log.info("Finish")
            break
        except Exception:
            log.exception("Failed in filler")
            raise


async def fresh_updater(store: Store, count: int = 10):
    rd = Readmanga(store)
    feedly = FeedlyClient()
    while True:
        try:
            await rd.feedly_worker(feedly, count)
            await sleep(timedelta(minutes=10).total_seconds())
        except Exception:
            log.exception("Failed in filler")
            raise


if __name__ == "__main__":
    db = LSM("../db.lsm")
    k = "naruto"
    print(Store(db).get_readmanga(k))
