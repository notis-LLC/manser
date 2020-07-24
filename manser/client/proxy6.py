import random
from datetime import datetime
from typing import Dict, List, Optional

import orjson
from aiohttp import ClientSession
from aiohttp_socks import ProxyConnector
from aioitertools.builtins import list
from pydantic import BaseModel, Field, IPvAnyAddress
from yarl import URL


class Proxy(BaseModel):
    id: str
    ip: IPvAnyAddress
    host: IPvAnyAddress
    port: int
    user: str
    password: str = Field(..., alias="pass")
    type: str
    country: str
    date: datetime
    date_end: datetime
    active: bool

    def url(self):
        schema = "socks5" if self.type == "socks" else "https"
        return URL.build(
            scheme=schema,
            user=self.user,
            password=self.password,
            host=str(self.host),
            port=self.port,
        )


class ProxyList(BaseModel):
    status: str
    balance: float
    list: Dict[str, Proxy]


class Proxy6:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.proxies: Optional[List[Proxy]] = None

    @property
    def _session(self):
        return ClientSession()

    async def init(self):
        self.proxies = await list(self.active())

    async def close(self):
        await self._session.close()

    async def getproxy(self):
        url = f"https://proxy6.net/api/{self.api_key}/getproxy"
        req = await self._session.get(url)
        return ProxyList(**await req.json(loads=orjson.loads))

    async def active(self) -> List[Proxy]:
        proxies = await self.getproxy()
        for proxy in proxies.list.values():
            if not proxy.active:
                continue
            yield proxy

    def choice(self) -> Proxy:
        return random.choice(self.proxies)

    def connector(self):
        proxy = self.choice()
        return ProxyConnector.from_url(str(proxy.url()), limit=1, limit_per_host=1)
