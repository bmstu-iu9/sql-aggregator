class Schema:
    def __init__(self, name: str, tables=None):
        self.name = name
        self.tables = tables or {}


class Table:
    def __init__(self, name: str, columns=None):
        self.name = name
        self.columns = columns or {}


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
