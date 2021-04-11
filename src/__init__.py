"""
Nominal docstring for tox purposes.
"""
from .pickle_shelf import SqlitePickleShelve
from .json_shelf import JsonSqliteShelve


__all__ = [
    "SqlitePickleShelve",
    "JsonSqliteShelve",
]
__version__ = "0.3.0"
