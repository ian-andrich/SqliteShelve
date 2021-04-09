import pickle
import re
import shelve
import sqlite3
import typing as t


class SyncStrategy(object):
    def __init__(self, shelf: shelve.Shelf, count: int=10000):
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
            
    def delete_statement(self):
        shelf = self.shelf
        pass


class SqliteShelve(shelve.Shelf):
    def __init__(self, name, tablename, *args, sync_strat=SyncStrategy, **kwargs):
        self.name = name
        self.tablename = tablename
        self.__conn__ = None
        self.__initializeddb__ = False
        self.__sync_strat__ = SyncStrategy(self)
    
    def sync(self):
        if self.__conn__ is None:
            raise ValueError("No connection established")
        self.__conn__.commit()
    
    def __getitem__(self, key: str) -> t.Any:
        try:
            result = self.__conn__.execute(f"SELECT val FROM {self.tablename} WHERE key=?", (key,)).fetchone()
            value = pickle.loads(result[0])
            return value
        except Exception:
            raise KeyError(f"Key {key} not found.")
    
    def __setitem__(self, key: str, val: Any):
        pickled_val = pickle.dumps(val)
        upsert_statement = f"INSERT INTO {self.tablename} (key, val) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET val=?"
        args = (key, pickled_val, pickled_val)
        self.__conn__.execute(upsert_statement, args)
        self.__sync_strat__.new_write()
            
    def __delitem__(self, key: str):
        del_statement = (f"DELETE FROM {self.tablename} WHERE key=?", (key,))
        self.__conn__.execute(*del_statement)
        self.__sync_strat__.new_write()
    
    def __contains__(self, key: str):
        results = self \
            .__conn__ \
            .execute(f"SELECT COUNT(*) FROM {self.tablename} WHERE key=?", (key,)) \
            .fetchone()[0]
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
        self.sync()
        self.__conn__.close()
        self.__conn__ = None
        
    def __initializedb__(self):
        assert self.__conn__ is not None
        try:
            self.__conn__.execute(f"CREATE TABLE IF NOT EXISTS {self.tablename} (key TEXT PRIMARY KEY NOT NULL, val BLOB);")
            self.__conn__.commit()
        except:
            self.__conn__.rollback()
        self.__initializeddb__ = True
        
    def keys(self) -> t.Iterator[str]:
        query = f"SELECT key FROM {self.tablename}"
        results = self.__conn__.execute(query)
        for result in results:
            yield result[0]
    
    def items(self) -> t.Iterator[t.Tuple[str, t.Any]]:
        query = f"SELECT key, val FROM {self.tablename}"
        cursor = self.__conn__.execute(query)
        for result in cursor:
            yield (result[0], pickle.loads(result[1]))
            
    def regex(self, regex: str) -> t.Iterator[t.Tuple[str, t.Any]]:
        """
        Does a full table scan performing the supplied regex on the keys.
        Yields key, object pairs as a tuple.
        """
        query = (f"SELECT key, val FROM {self.tablename} WHERE key REGEX ?", (regex,))
        for r in self.__conn__.execute(*query):
            yield (r[0], pickle.loads(r[1]))