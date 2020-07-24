import logging
from datetime import timedelta
from functools import partial

from starlette.config import Config
from starlette.datastructures import Secret

# Config will be read from environment variables and/or ".env" files.
config = Config(".env")

DEBUG = config("DEBUG", cast=bool, default=False)
TESTING = config("TESTING", cast=bool, default=False)

HOST = config("HOST", cast=str, default="127.0.0.1")
PORT = config("PORT", cast=int, default=8080)

LOG_LEVEL = config(
    "LOG_LEVEL",
    cast=logging.getLevelName,
    default=logging.DEBUG if DEBUG else logging.INFO,
)

PROXY6_TOKEN = config("PROXY6_TOKEN", cast=Secret)
DBNAME = config("DBNAME", cast=str, default="db.lsm")


UPDATE_INTERVAL_HOURS = config("UPDATE_INTERVAL_HOURS", default=4, cast=int)
UPDATE_INTERVAL = timedelta(hours=UPDATE_INTERVAL_HOURS)

WORKERS = config("WORKERS", default=2, cast=int)
