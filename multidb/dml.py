import logging

from . import expression as expr
from . import join as jn
from . import structures as st
from . import symbols as ss
from . import utils
from ._logger import ParserLogger
from .exceptions import UnreachableException, SemanticException
from itertools import combinations_with_replacement


class Select:
    logger: ParserLogger = logging.getLogger('selection')

    class PDNF:
        def __init__(self, expression):
            assert isinstance(expression, expr.BooleanExpression)

            self.raw_expression = expression
            self.base_expressions = self.get_base_expressions(expression)

            self.true_combination = [
                vector
                for vector in combinations_with_replacement(
                    [False, None, True],
                    len(self.base_expressions)
                )
                for value in [expression.calculate(list(vector))]
                if value
            ]

        def get_base_expressions(self, expression):
            if isinstance(expression, expr.DoubleBooleanExpression):
                left = self.get_base_expressions(expression.left)
                right = self.get_base_expressions(expression.right)
                return left + right
            elif isinstance(expression, expr.Not):
                return self.get_base_expressions(expression.value)
            elif isinstance(expression, (
                    expr.BasePredicate,
                    expr.NumericExpression,
                    st.Column,
            )):
                return [expression]
            return []

    def __init__(self, cc, select_list, from_, where=None, group=None, having=None):
        if len(from_) != 1:
            self.logger.error('Support only one one table or join')
            return
        self.cc = cc  # ControlCenter

        self.select_list = select_list
        self.from_ = from_
        self.where = where
        self.group = group
        self.having = having

        self.alias_table = {}
        self.alias_selection = {}

        self.name_to_table = {}

        self.full_selection_list = []
        self.full_table_list = []

    def validate(self):
        self.validate_from()
        self.validate_select_list()
        self.validate_where()

    def validate_from(self):
        self.from_ = [
            self.check_all_tables(tbl)[1] or tbl
            for tbl in self.from_
            for _ in [self.full_table_list.append([])]
        ]

    def check_all_tables(self, table):
        """
        Грязная функция - меняет состояния уже существующих объектов
        """
        if isinstance(table, utils.NamingChain):
            return self.check_table(table)
        elif isinstance(table, jn.BaseJoin):
            left_name, left_obj = self.check_all_tables(table.left)
            if left_obj:
                table.left = left_obj
            right_name, right_obj = self.check_all_tables(table.right)
            if right_obj:
                table.right = right_obj
            if isinstance(table, jn.QualifiedJoin):
                if not isinstance(table.specification, (
                        expr.BooleanExpression,
                        expr.BasePredicate,
                        expr.Column,
                )):
                    self.logger.error('Support join condition only boolean expression or column')
                else:
                    table.specification = self.validate_expression(table.specification.convolution)
                    if isinstance(table.specification, expr.BooleanExpression):
                        table.specification = self.PDNF(table.specification)

            return None, None

    def check_table(self, table_naming_chain, only_get=False):
        """
        1) Находим полное имя таблицы,
        для alias возможно найти сразу таблицу
        2) По полному имени ищем таблицу в словаре
        3) Если таблицы нет, то создаем ее
        и кладем в словарь и список
        4) Если таблица имеет короткое имя,
        то сохроняем ее под этим именем в self.alias_table,
        иначе сохраняем по
        """
        name = table_naming_chain.get_data()
        alias = table_naming_chain.short_name

        table_obj = None
        dbms = db = schema = table = None

        if len(name) == 4:  # Full name
            dbms, db, schema, table = name

        elif len(name) == 3:  # Alias db
            alias_db, schema, table = name
            find = self.cc.local_alias['db'].get(alias_db)
            if not find:
                self.logger.error('Alias db %s not found', alias_db)
                return None, None
            dbms, db = find
        elif len(name) == 2:  # Alias schema
            alias_schema, table = name
            find = self.cc.local_alias['schema'].get(alias_schema)
            if not find:
                self.logger.error('Alias schema %s not found', alias_schema)
                return None, None
            dbms, db, schema = find
        elif len(name) == 1:  # Alias table
            alias_table, = name
            table_obj = self.alias_table.get(alias_table)
            if not table_obj:
                find = self.cc.local_alias['table'].get(alias_table)
                if not find:
                    self.logger.error('Alias table %s not found', alias_table)
                    return None, None
                dbms, db, schema, table = find
        else:
            self.logger.error('Wrong naming chain for table: %s', table_naming_chain)
            return None, None

        full_name = utils.NamingChain(dbms, db, schema, table)
        table_obj = table_obj or self.name_to_table.get(full_name.get_data())

        if only_get:
            if not table_obj:
                self.logger.error('Table %s not found in FROM', table_naming_chain)
                return None, None
            return full_name, table_obj

        if not table_obj:
            # Если dbms есть в псевдонимах dbms, то используем оригинал
            dbms = self.cc.local_alias['dbms'].get(dbms, dbms)
            dbms_obj = self.cc.sources.get(dbms)
            if not dbms_obj:
                self.logger.error('DBMS %s not found', dbms)
                return None, None
            try:
                table_obj = st.Table(dbms_obj, db, schema, table)
            except SemanticException:
                return None, None
            if full_name.get_data() in self.name_to_table:
                self.logger.error('Many use table %s not supported', table_naming_chain)
                return None, None
            self.name_to_table[full_name.get_data()] = table_obj

        self.full_table_list[-1].append(table_obj)

        if alias:
            if alias in self.alias_table:
                self.logger.error('Duplicate alias table %s', alias)
                return None, None
            self.alias_table[alias] = table_obj
        elif str(full_name) not in self.alias_table:
            self.alias_table[str(full_name)] = table_obj

        return full_name, table_obj

    def validate_select_list(self):
        """
        В select_list, все выражения типа Column()
        заменяются на объект колонки из таблицы,
        все такие колонки помечаются как используемые
        """
        select_list = []

        if isinstance(self.select_list, str):  # all columns for all tables
            assert self.select_list == ss.asterisk
            assert len(self.select_list) == 1
            for level in self.full_table_list:
                for tbl in level:
                    for column in tbl.columns:
                        column.used = True
                    select_list.extend(tbl.columns)
        else:
            for is_qualified_asterisk, selection in self.select_list:
                if is_qualified_asterisk:  # all column for one table
                    check = self.check_table(selection, True)
                    if not check:
                        continue
                    _, tbl = check
                    for column in tbl.columns:
                        column.used = True
                    select_list.extend(tbl.columns)
                else:  # expression
                    short_name = selection.short_name
                    repr_name = repr(selection)
                    e = self.validate_expression(selection.convolution)
                    if short_name:
                        self.alias_selection[short_name] = e
                    e.as_(short_name or repr_name)
                    select_list.append(e)
        self.select_list = select_list

    def validate_expression(self, expression):
        """
        Грязная функция - меняет состояния уже существующих объектов
        """
        if isinstance(expression, expr.Column):
            name = expression.value
            tuple_name = name.get_data()
            assert 2 <= len(tuple_name) <= 5
            *table_name, column_name = tuple_name
            full_table_name, table_obj = self.check_table(utils.NamingChain(*table_name), True)
            if not table_obj:
                return expression

            column: st.Column = table_obj.name_to_column.get(column_name)
            if not column:
                self.logger.error('Column %s not found', name)
                return expression
            column.used = True
            return column

        elif isinstance(expression, expr.NumericExpression):
            if isinstance(expression, expr.UnarySign):
                expression.value = self.validate_expression(expression.value)
            elif isinstance(expression, expr.DoubleNumericExpression):
                expression.left = self.validate_expression(expression.left)
                expression.right = self.validate_expression(expression.right)
            else:
                raise UnreachableException()

        elif isinstance(expression, expr.BooleanExpression):
            if isinstance(expression, expr.Not):
                expression.value = self.validate_expression(expression.value)
            elif isinstance(expression, expr.Is):
                expression.left = self.validate_expression(expression.left)
            elif isinstance(expression, expr.DoubleBooleanExpression):
                expression.left = self.validate_expression(expression.left)
                expression.right = self.validate_expression(expression.right)
            else:
                raise UnreachableException()

        elif isinstance(expression, expr.ComparisonPredicate):
            expression.left = self.validate_expression(expression.left)
            expression.right = self.validate_expression(expression.right)
        return expression

    def validate_where(self):
        if not self.where:
            return
        if not isinstance(self.where, (
            expr.BooleanExpression,
            expr.BasePredicate,
            expr.Column,
        )):
            self.logger.error('Support where condition only boolean expression or column')
            return
        self.where = self.where and self.validate_expression(self.where.convolution)
        if isinstance(self.where, expr.BooleanExpression):
            self.where = self.PDNF(self.where)
