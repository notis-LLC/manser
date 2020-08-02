import pytest

pytestmark = pytest.mark.asyncio


async def test_proxy6(proxy6):
    proxies = await proxy6.getproxy()
    assert proxies.balance > 0
    assert len(proxies.list) > 0
