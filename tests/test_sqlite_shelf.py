import pytest
from ..src import SqliteShelve


@pytest.fixture
def blank_shelf():
    shelf = SqliteShelve(":memory:", "test")
    shelf.open()
    yield shelf
    shelf.close()


@pytest.fixture
def loaded_shelf(blank_shelf):
    for x in range(1000):
        blank_shelf[f"{x}"] = f"Hello {x}"
    blank_shelf.sync()
    return blank_shelf


def test_contains(loaded_shelf):
    assert "5" in loaded_shelf


def test_get(loaded_shelf):
    assert loaded_shelf["5"] == "Hello 5"


def test_items(loaded_shelf):
    for key, item in loaded_shelf.items():
        assert key in item


def test_keys(loaded_shelf):
    for key in loaded_shelf.keys():
        pass


def test_deletion(loaded_shelf):
    del loaded_shelf["5"]
    assert "5" not in loaded_shelf


def test_regex(loaded_shelf):
    results = dict(loaded_shelf.regex("5$"))
    assert "5" in results