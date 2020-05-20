import logging
from collections import namedtuple
from itertools import groupby
from operator import itemgetter

import pyodbc

from .parser import IndexParser, kw


class Index:
    BTREE = 0

    def __init__(self, name, columns, is_unique, kind):
        self.name = name
        self.columns = columns
        self.is_unique = is_unique
        self.kind = kind


IndexColumn = namedtuple('IndexColumn', 'name order')


class BaseDialect:
    DBMS_TO_DRIVER = {}

    SQL_GET_SCHEMAS = (
        'select schema_name '
        'from information_schema.schemata;'
    )
    SQL_GET_TABLES = (
        "select "
        "table_name "
        "from information_schema.tables "
        "where "
        "table_schema = '{schema}';"
    )
    SQL_GET_COLUMNS = (
        "select "
        "  column_name"
        ", is_nullable"
        ", data_type"
        "from information_schema.columns "
        "where "
        "table_schema = '{schema}' "
        "and table_name = '{table}' "
        "order by ordinal_position;"
    )

    @classmethod
    def without_conn_string(cls, server, database, user, password, driver=None):
        driver = driver or cls.DBMS_TO_DRIVER[cls.__name__]
        conn_str = ';'.join(
            '='.join([k, v])
            for k, v in [
                ('DRIVER', driver),
                ('DATABASE', database),
                ('SERVER', server),
                ('UID', user),
                ('PWD', password),
            ]
            if v
        )
        return cls(conn_str)

    def __init__(self, conn_str):
        self.connection: pyodbc.Connection = pyodbc.connect(conn_str)
        self.default_cursor: pyodbc.Cursor = self.connection.cursor()

    def all_schemas(self):
        self.default_cursor.execute(self.SQL_GET_SCHEMAS)
        return [schema for schema, in self.default_cursor.fetchall()]

    def all_tables(self, schema):
        self.default_cursor.execute(self.SQL_GET_TABLES.format(schema=schema))
        return [schema for schema, in self.default_cursor.fetchall()]

    def all_columns(self, schema, table):
        self.default_cursor.execute(self.SQL_GET_COLUMNS.format(schema=schema, table=table))
        return [(name, is_null, dtype) for name, is_null, dtype in self.default_cursor.fetchall()]

    def get_indexes(self, schema, table):
        return

    def __del__(self):
        self.default_cursor.close()
        self.connection.close()


class PostgreSQL(BaseDialect):
    logger = logging.getLogger('psql_dialect')
    SUPPORTED_INDEX_TYPE = {
        'btree': Index.BTREE
    }

    def get_indexes(self, schema, table):
        query = (
            "select"
            "  indexname"
            ", indexdef"
            "from pg_indexes "
            "where "
            "schemaname='{}' and tablename='{}';"
        ).format(schema, table)
        self.default_cursor.execute(query)
        indexes = []
        for name, define, in self.default_cursor.fetchall():
            parser = IndexParser.build(define)
            try:
                data = parser.program()
            except Exception as ex:
                self.logger.warning('Parse index %s failed:\n%s', define, ex)
                continue
            columns, is_unique, method = data
            new_columns = [
                IndexColumn(column, collate)
                for column, _, _, asc_desc, _ in columns
                for collate in [
                    True
                    if asc_desc == kw.ASC else
                    False
                    if asc_desc == kw.DESC else
                    True  # Default
                ]
            ]
            method = self.SUPPORTED_INDEX_TYPE.get(method.lower())
            if method:
                indexes.append(Index(name, new_columns, is_unique, method))
        return indexes


class MySQL(BaseDialect):
    @staticmethod
    def __check_data(arr):
        assert all(arr[0] == a for a in arr)
        return arr[0]

    SUPPORTED_INDEX_TYPE = {
        'btree': Index.BTREE
    }

    def get_indexes(self, schema, table):
        query = (
            "select"
            "  index_name"  # 0
            ", not non_unique"  # 1
            ", collation"  # 2
            ", index_type"  # 3
            ", column_name"  # 4
            ", seq_in_index"  # 5
            "from information_schema.statistics "
            "where "
            "table_schema='{}' "
            "and table_name='{}' "
            "order by index_name, seq_in_index;"
        ).format(schema, table)
        self.default_cursor.execute(query)
        return [
            Index(group, columns, is_unique, kind)
            for group, data in groupby(
                self.default_cursor.fetchall(),
                key=itemgetter(0)
            )
            for columns, uniques, index_types in zip(*[
                (IndexColumn(col_name, collation), bool(unique), index_type)
                for _, unique, collation, index_type, col_name, _ in data
                for collation in [True if collation == 'A' else False if collation == 'D' else None]
            ])
            for kind in [self.SUPPORTED_INDEX_TYPE.get(
                self.__check_data(index_types).lower()
            )]
            for is_unique in [self.__check_data(uniques)]
            if kind is not None
        ]


class SQLite(BaseDialect):
    pass
