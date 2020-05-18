class AsMixin:
    def __init__(self, *args, **kwargs):
        self.short_name = None

    def as_(self, name):
        self.short_name = name


class NameChain(AsMixin):
    def __init__(self, *args):
        super().__init__()
        self.chain = list(args)

    @staticmethod
    def __map_other(other):
        return (
            other.chain
            if isinstance(other, NameChain) else
            list(other)
            if isinstance(other, (list, tuple)) else
            [other]
        )

    def push_first(self, other):
        self.chain = self.__map_other(other) + self.chain

    def push_last(self, other):
        self.chain = self.chain + self.__map_other(other)


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
