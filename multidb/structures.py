from . import mixins


class NamingChain(mixins.AsMixin):
    def __init__(self, *args):
        super().__init__()
        self.chain = list(args)

    @staticmethod
    def __map_other(other):
        return (
            other.chain
            if isinstance(other, NamingChain) else
            list(other)
            if isinstance(other, (list, tuple)) else
            [other]
        )

    def push_first(self, other):
        self.chain = self.__map_other(other) + self.chain

    def push_last(self, other):
        self.chain = self.chain + self.__map_other(other)

    def get_data(self):
        return tuple(self.chain)

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, self)

    def __str__(self):
        return '.'.join(self.chain)


class DBMS:
    def __init__(self, name, dbs):
        self.name = name
        self._dbs = dbs


class DB:
    def __init__(self, name: str, dbms: DBMS, schemas=None):
        self.name = name
        self.dbms = dbms
        self._schemas = schemas

    @property
    def schemas(self):
        if self._schemas is None:
            self._schemas = self.get_all_schemas()
        return self._schemas

    def get_all_schemas(self):
        pass


class Schema:
    default = 'public'

    def __init__(self, name: str, db: DB, tables=None):
        self.name = name
        self.db = db
        self._tables = tables

    @property
    def tables(self):
        if self._tables is None:
            self._tables = self.get_all_tables()
        return self._tables

    def get_all_tables(self):
        pass


class Table:
    def __init__(self, name: str, schema: Schema, columns=None):
        self.name = name
        self.schema = schema
        self.columns = columns or {}

    def get_column(self, column):
        pass


class Column:
    PRIMARY = 0
    INDEXED = 1
    COMMON = 2

    @classmethod
    def primary(cls, name: str):
        return Column(name, cls.PRIMARY)

    @property
    def is_primary(self):
        return self.kind == self.PRIMARY

    @classmethod
    def indexed(cls, name: str):
        return Column(name, cls.INDEXED)

    @property
    def is_indexed(self):
        return self.kind == self.INDEXED

    @classmethod
    def common(cls, name: str):
        return Column(name, cls.COMMON)

    @property
    def is_common(self):
        return self.kind == self.COMMON

    def __init__(self, name: str, kind: int):
        self.name = name
        self.kind = kind
