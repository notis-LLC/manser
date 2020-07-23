import string
from datetime import datetime

import pytest

from manser.client.manga.abc import BaseLatestValidator
from manser.client.store import Store


@pytest.fixture
def data():
    data_list = [
        (1, 3, "Третья", datetime(2000, 1, 3), "http://test.http/3"),
        (1, 2, "Вторая", datetime(2000, 1, 2), "http://test.http/2"),
        (1, 1, "Первая", datetime(2000, 1, 1), "http://test.http/1"),
    ]
    return [
        BaseLatestValidator(tome=tome, number=number, name=name, date=date, href=href)
        for tome, number, name, date, href in data_list
    ]


@pytest.fixture
def save(store: Store, data):
    for slug in (
        "test-manga",
        "another-manga",
        "yet-another",
        *list(string.ascii_lowercase),
    ):
        store.save("test", slug, data)


def test_store(store: Store, save):
    slug = "test-manga"
    loads = list(store.load("test", slug))
    assert len(loads) == 3
    assert loads[0].name == "Третья"
    assert loads[0].number == 3.0
    assert loads[0].tome == 1
