import logging

import pyodbc
import pypika as pk
from pypika import dialects as pika_dialects

from . import dialect
from . import mixins as mx
from .exceptions import SemanticException
from . import utils


class DBMS:
    TYPE_TO_DIALECT = {
        'psql':  dialect.PostgreSQL,
        'mysql': dialect.MySQL,
    }
    TYPE_TO_PIKA = {
        'psql':  pika_dialects.PostgreSQLQuery,
        'mysql': pika_dialects.MySQLQuery
    }

    def __init__(self, name, connect_data):
        self.connections = {}
        kind_dbms = connect_data.pop('type').lower()
        self.dialect = self.TYPE_TO_DIALECT[kind_dbms](**connect_data)
        self.sql = self.TYPE_TO_PIKA[kind_dbms]
        self.tables = {}
        self.name = name

    def connect(self, db):
        conn = self.connections.get(db)
        if conn is None:
            self.connections[db] = conn = pyodbc.connect(self.dialect.conn_str(db))
        return conn

    def __del__(self):
        for conn in self.connections.values():
            conn.close()


class Table:
    IS_SQLITE = False
    count = 0
    logger = logging.getLogger('table')

    def __init__(self, dbms: DBMS, db: str, schema: str, table: str):
        self.dbms = dbms
        self.connection = dbms.connect(db)
        self.cursor: pyodbc.Cursor = self.connection.cursor()
        dbms.tables.setdefault(db, {}).setdefault(schema, {})[table] = self

        self.db = db
        self.schema = schema
        self.table = table

        self._db = pk.Database(db)
        self._schema = pk.Schema(schema)
        self._table = pk.Table(table, self._schema, query_cls=self.dbms.sql)

        self.sqlite_table = pk.Table('{}_{}'.format(table, Table.count))

        self.indexes = self.dbms.dialect.get_indexes(self.cursor, schema, table)
        self.columns, self.name_to_column = self.__get_columns()

        try:
            self.test_table(self.cursor)
        except Exception as ex:
            msg = 'Table {}.{}.{} not found:\nException:{}'.format(db, schema, table, ex)
            self.logger.error(msg)
            raise SemanticException(msg)

        self.filters = []

        Table.count += 1

    def get_sql(self):
        return self.sqlite_table.get_sql() if Table.IS_SQLITE else self._table.get_sql()

    def __get_columns(self):
        raw_columns = self.dbms.dialect.all_columns(self.cursor, self.schema, self.table)
        if not raw_columns:
            msg = 'Columns not found for table {}.{}.{}'.format(self.db, self.schema, self.table)
            self.logger.error(msg)
            raise SemanticException(msg)
        columns = []
        name_to_column = {}
        for column_name, is_null, dtype, max_len, max_size, supported in raw_columns:
            found_indexes = []
            for index in self.indexes:
                for idx_column in index.columns:
                    if column_name == idx_column.name:
                        found_indexes.append(index)
                        break

            column = Column(self, column_name, is_null, dtype, max_len, max_size, found_indexes, supported)
            columns.append(column)
            name_to_column[column_name] = column
        return columns, name_to_column

    def test_table(self, cursor):
        query = (self.dbms.sql
                 .from_(self._table)
                 .select('*')
                 .limit(1))
        cursor.execute(query.get_sql())
        cursor.fetchall()

    @utils.lazy_property
    def selected_columns(self):
        columns = [
            column
            for column in self.columns
            if column.used and (column.visible or column.count_used > 0)
        ]
        for i, column in enumerate(columns):
            column.idx = i
        return columns

    def __del__(self):
        try:
            self.cursor.close()
        except pyodbc.ProgrammingError:
            pass

    def full_name(self):
        return self.dbms.name, self.db, self.schema, self.table

    @utils.lazy_property
    def select_query(self):
        q = self._table.select(*[
            column.pika()
            for column in self.selected_columns
        ])
        for f in self.filters:
            q = q.where(f.pika())
        return q

    @utils.lazy_property
    def create_query(self):
        columns = pk.Columns(*[
            (column.name, column.type)
            for column in self.selected_columns
        ])
        return pk.SQLLiteQuery.create_table(self.sqlite_table).columns(*columns)

    @utils.lazy_property
    def insert_query(self):
        return 'INSERT INTO {} VALUES ({})'.format(
            self.sqlite_table.get_sql(),
            ', '.join(['?'] * len(self.selected_columns))
        )

    @utils.lazy_property
    def size(self):
        return len(self.selected_columns)

    def __repr__(self):
        return 'Table({}.{}.{}.{}, where={})'.format(*self.full_name(), self.filters)


class Column(mx.AsMixin):

    def __init__(self, table: Table, name: str, is_null: bool, dtype: str,
                 max_len: int, max_size: int, indexes=None, supported=True):
        super().__init__()
        self.name = name
        self.is_null = is_null
        self.dtype = dtype

        self.indexes = indexes or []
        self.table = table

        self.max_len = max_len
        self.max_size = max_size  # max_len * 4 for unicode

        self.supported = supported

        self._used = False
        self.visible = False
        self.count_used = 0

        self.idx = None

    @utils.lazy_property
    def type(self):
        return ('{}({})'.format(dialect.BaseDialect.BASE_TYPE_TO_SQLITE_TYPE[self.dtype], self.max_len)
                if self.max_len is not None else
                dialect.BaseDialect.BASE_TYPE_TO_SQLITE_TYPE[self.dtype])

    def pika(self):
        return pk.Field(self.name, table=self.table.sqlite_table) if Table.IS_SQLITE else pk.Field(self.name)

    @property
    def used(self):
        return self._used

    @used.setter
    def used(self, value):
        if not self.supported:
            self.table.logger.error(
                'Data type `%s` not supported. For column %s.%s',
                self.dtype,
                '.'.join(self.table.full_name()),
                self.name
            )
        self._used = value

    # def __repr__(self):
    #     return (
    #         'Column({}.{}'
    #         ', is_null={}'
    #         ', type={}'
    #         ', size={}'
    #         ', indexes={}'
    #         ', supported={}'
    #         ', count_used={}'
    #         ', visible={})'
    #     ).format(
    #         '.'.join(self.table.full_name()),
    #         self.name,
    #         self.is_null,
    #         self.dtype,
    #         self.max_size,
    #         self.indexes,
    #         self.supported,
    #         self.count_used,
    #         self.visible
    #     )

    def __eq__(self, other):
        return self.name == other.name and self.table is other.table

    def __repr__(self):
        return 'Column({}.{})'.format(self.table.table, self.name)
