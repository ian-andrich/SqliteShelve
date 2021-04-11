import pytest
from ..src import JsonSqliteShelve


@pytest.fixture
def blank_shelf():
    shelf = JsonSqliteShelve(":memory:", "test", sync_count=10)
    shelf.open()
    yield shelf
    shelf.close()


@pytest.fixture
def loaded_shelf(blank_shelf):
    for x in range(1000):
        blank_shelf[f"{x}"] = {"a": f"Hello {x}"}
    blank_shelf.sync()
    return blank_shelf


def test_contains(loaded_shelf):
    assert "5" in loaded_shelf


def test_get(loaded_shelf):
    assert loaded_shelf["5"]["a"] == "Hello 5"


def test_inserting_unjsonable_item_raises(blank_shelf):
    class Blah():
        pass

    with pytest.raises(TypeError):
        blank_shelf["a"] = Blah()


def test_items(loaded_shelf):
    for key, item in loaded_shelf.items():
        assert key in item["a"]


def test_keys(loaded_shelf):
    for key in loaded_shelf.keys():
        pass


def test_deletion(loaded_shelf):
    del loaded_shelf["5"]
    assert "5" not in loaded_shelf


def test_regex(loaded_shelf):
    results = dict(loaded_shelf.regex("5$"))
    assert "5" in results


def test_sync_raises():
    shelf = JsonSqliteShelve(":memory:", "test")
    with pytest.raises(ValueError):
        shelf.sync()


def test_context_manager():
    shelf = JsonSqliteShelve(":memory:", "test")
    with shelf:
        pass


def test_getter_raises_key_error(loaded_shelf):
    with pytest.raises(KeyError):
        loaded_shelf["a"]


def test_sync_strat_raises_valueerror_on_low_count():
    with pytest.raises(ValueError):
        shelf = JsonSqliteShelve(":memory:", "test", sync_count=-10)
