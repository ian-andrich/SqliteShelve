import pickle
import re
import sqlite3
import typing as t
import abc


class ShelfBase(abc.ABC):  # pragma: no cover
    """
    Needed to avoid circular imports
    """

    @abc.abstractmethod
    def sync(self):
        pass


class SyncStrategy(object):
    """
    Responsible for periodically syncing to disk
    """

    def __init__(self, shelf: ShelfBase, count: int = 10000):  # type: ignore
        if count <= 0:
            raise ValueError(f"Count '{count}' must be a positive int")
        self.shelf = shelf
        self.__count__ = count
        self.__current__ = 0

    def new_write(self):
        shelf = self.shelf
        max_count = self.__count__
        cur_count = self.__current__
        if cur_count > max_count:
            self.__current__ = 0
            shelf.sync()
        else:
            self.__current__ += 1


class BaseShelf(ShelfBase):
    """
    Provides a shelf interface for KV storage in sqlite3
    """

    def __init__(
        self,
        name,
        tablename,
        sync_strat=SyncStrategy,
        sync_count: int = 10000,
        loader=pickle.loads,
        dumper=pickle.dumps,
    ):
        self.name = name
        self.tablename = tablename
        self.__conn__: t.Optional[sqlite3.Connection] = None
        self.__initializeddb__ = False
        self.__sync_strat__ = SyncStrategy(self, count=sync_count)
        self._loads = loader
        self._dumps = dumper

    def sync(self):
        if self.__conn__ is None:
            raise ValueError("No connection established. Open shelf first")
        self.__conn__.commit()

    def __getitem__(self, key: str) -> t.Any:
        try:
            assert self.__conn__ is not None
            result = self.__conn__.execute(
                f"SELECT val FROM {self.tablename} WHERE key=?", (key,)
            ).fetchone()
            value = self._loads(result[0])
            return value
        except Exception:
            raise KeyError(f"Key {key} not found.")

    def __setitem__(self, key: str, val: t.Any):
        pickled_val = self._dumps(val)
        upsert_statement = (
            f"INSERT INTO {self.tablename} (key, val) VALUES"
            f" (?, ?) ON CONFLICT(key) DO UPDATE SET val=?"
        )
        args = (key, pickled_val, pickled_val)
        assert self.__conn__ is not None
        self.__conn__.execute(upsert_statement, args)
        self.__sync_strat__.new_write()

    def __delitem__(self, key: str):
        del_statement = (f"DELETE FROM {self.tablename} WHERE key=?", (key,))
        assert self.__conn__ is not None
        self.__conn__.execute(*del_statement)
        self.__sync_strat__.new_write()

    def __contains__(self, key: object) -> bool:
        assert self.__conn__ is not None
        results = self.__conn__.execute(
            f"SELECT COUNT(*) FROM {self.tablename} WHERE key=?", (key,)
        ).fetchone()[0]
        return results > 0

    def __enter__(self):
        self.open()

    def __exit__(self, exceptiontype, exceptionvalue, traceback):
        self.close()

    def open(self) -> None:
        # Only do something if it isn't open
        self.__conn__ = sqlite3.connect(self.name, isolation_level="DEFERRED")

        # Add regexp functionality
        def regexp(expr, item):
            reg = re.compile(expr)
            return reg.search(item) is not None

        self.__conn__.create_function("REGEXP", 2, regexp)

        if not self.__initializeddb__:
            self.__initializedb__()
            self.__initializeddb__ = True

    def close(self) -> None:
        assert self.__conn__ is not None
        self.sync()
        self.__conn__.close()
        self.__conn__ = None

    def __initializedb__(self):
        assert self.__conn__ is not None
        self.__conn__.execute(
            f"CREATE TABLE IF NOT EXISTS {self.tablename}"
            f" (key TEXT PRIMARY KEY NOT NULL, val BLOB);"
        )
        self.__conn__.commit()
        self.__initializeddb__ = True

    def keys(self) -> t.Generator[str, None, None]:
        query = f"SELECT key FROM {self.tablename}"
        assert self.__conn__ is not None
        results = self.__conn__.execute(query)
        for result in results:
            yield result[0]

    def items(self) -> t.Generator[t.Tuple[str, t.Any], None, None]:
        query = f"SELECT key, val FROM {self.tablename}"
        assert self.__conn__ is not None
        cursor = self.__conn__.execute(query)
        for result in cursor:
            yield (result[0], self._loads(result[1]))

    def regex(self, regex: str) -> t.Iterator[t.Tuple[str, t.Any]]:
        """
        Does a full table scan performing the supplied regex on the keys.
        Yields key, object pairs as a tuple.
        """
        query = (f"SELECT key, val FROM {self.tablename} WHERE key REGEXP ?", (regex,))
        assert self.__conn__ is not None
        for r in self.__conn__.execute(*query):
            yield (r[0], self._loads(r[1]))
