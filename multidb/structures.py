import logging

import pyodbc
import pypika as pk
from pypika import dialects as pika_dialects

from . import dialect
from .exceptions import SemanticException
from . import mixins as mx


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
        kind_dbms = connect_data.pop('type').lower()
        self.dialect = self.TYPE_TO_DIALECT[kind_dbms](**connect_data)
        self.sql = self.TYPE_TO_PIKA[kind_dbms]

        self.name = name
        self.connections = {}

    def connect(self, db):
        conn = self.connections.get(db)
        if conn is None:
            self.connections[db] = conn = pyodbc.connect(self.dialect.conn_str(db))
        return conn

    def __del__(self):
        for conn in self.connections.values():
            conn.close()


class Table:
    logger = logging.getLogger('table')

    def __init__(self, dbms: DBMS, db: str, schema: str, table: str):
        self.dbms = dbms
        self.connection = dbms.connect(db)
        self.cursor: pyodbc.Cursor = self.connection.cursor()

        self.db = db
        self.schema = schema
        self.table = table

        self._db = pk.Database(db)
        self._schema = pk.Schema(schema, self._db)
        self._table = pk.Table(table, self._schema)

        self.indexes = self.dbms.dialect.get_indexes(self.cursor, schema, table)
        self.columns, self.name_to_column = self.__get_columns()

        try:
            self.test_table(self.cursor)
        except Exception as ex:
            msg = 'Table {}.{}.{} not found:\nException:{}'.format(db, schema, table, ex)
            self.logger.error(msg)
            raise SemanticException(msg)

        self.use_columns = {}

    def __get_columns(self):
        raw_columns = self.dbms.dialect.all_columns(self.cursor, self.schema, self.table)
        if not raw_columns:
            msg = 'Columns not found for table {}.{}.{}'.format(self.db, self.schema, self.table)
            self.logger.error(msg)
            raise SemanticException(msg)
        columns = []
        name_to_column = {}
        for column_name, is_null, dtype in raw_columns:
            found_index = None
            for index in self.indexes:
                for idx_column in index.columns:
                    if column_name == idx_column.name:
                        found_index = index
                        break
                else:
                    continue
                break
            column = Column(self, column_name, is_null, dtype, found_index)
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

    def __del__(self):
        self.cursor.close()


class Column(mx.AsMixin):
    def __init__(self, table: Table, name: str, is_null: bool, dtype: int, index=None):
        super().__init__()
        self.name = name
        self.is_null = is_null
        self.dtype = dtype

        self.index = index
        self.table = table

    def copy(self, table):
        return Column(table, self.name, self.is_null, self.dtype, self.index)
