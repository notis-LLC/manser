import logging
from os import environ

from starlette.config import Config
from starlette.datastructures import Secret

# Config will be read from environment variables and/or ".env" files.
config = Config(".env")

DEBUG = config("DEBUG", cast=bool, default=False)
TESTING = config("TESTING", cast=bool, default=False)

HOST = config("HOST", cast=str, default="127.0.0.1")
PORT = config("PORT", cast=int, default=8080)

LOG_LEVEL = logging.DEBUG if DEBUG else logging.INFO

PROXY6_TOKEN = config("PROXY6_TOKEN", cast=Secret)
DBNAME = config("DBNAME", cast=str, default="db.lsm")
