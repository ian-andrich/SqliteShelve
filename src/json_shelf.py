from .base_shelf import BaseShelf, SyncStrategy


import json


class JsonSqliteShelve(BaseShelf):
    def __init__(
        self,
        name,
        tablename,
        sync_strat=SyncStrategy,
        sync_count=10000,
        loader=json.loads,
        dumper=json.dumps,
    ):
        super().__init__(
            name,
            tablename,
            sync_strat=sync_strat,
            sync_count=sync_count,
            loader=loader,
            dumper=dumper,
        )
