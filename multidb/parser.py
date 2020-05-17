import logging

from . import _logger
from . import lexer
from .exceptions import NotSupported, FatalSyntaxException, SyntaxException
from itertools import product
from . import keywords as kw
from . import symbols as ss
from . import expression as expr
from . import token as tk
from . import parse_data
# noinspection PyTypeChecker
logger = logging.getLogger('parser')  # type: _logger.ParserLogger


class CmpLexer(lexer.Lexer):
    STRICT = 0
    SAFE = 1
    OPTIONAL = 2

    def __init__(self, pos, interval=None, last_interval=None, current_tokens=None):
        super().__init__(pos, interval, last_interval, current_tokens)
        self.mode = self.STRICT

    @property
    def optional(self):
        self.mode = self.OPTIONAL
        return self

    @property
    def safe(self):
        self.mode = self.SAFE
        return self

    def check(self, other):
        value = None
        fail = True
        other = other if isinstance(other, (tuple, list)) else (other,)
        for token, kind in product(self.current_tokens, other):
            if token.check_type(kind):
                value = token.decode
                fail = False
                break
        return fail, value

    def __rshift__(self, other):
        fail, value = self.check(other)
        if fail:
            if self.mode == self.OPTIONAL:
                self.mode = self.STRICT
                return
            msg = 'Current tokens ({}) not in required ({})'.format(
                ', '.join(str(i) for i in self.current_tokens),
                ', '.join(i.__name__ if isinstance(i, type) else i for i in other)
            )
            if self.mode == self.SAFE:
                logger.current_token.warning(msg)
            elif self.mode == self.STRICT:
                logger.fatal(msg)
                raise FatalSyntaxException(msg)

        self.mode = self.STRICT
        self.next()
        return value

    def __eq__(self, other):
        return not self.check(other)[0]


class Parser:
    def __init__(self, lex: CmpLexer):
        logger.set_lexer(lex)
        self.token = lex
        self.data = parse_data.ParseData()

    def program(self):
        #   <select>
        # | <insert>
        # | <update>
        # | <delete>
        self.token.next()

        if self.token == kw.SELECT:
            self.select()

        elif self.token == kw.INSERT:
            self.insert()

        elif self.token == kw.UPDATE:
            self.update()

        elif self.token == kw.DELETE:
            self.delete()

        self.token >> tk.EndToken

    def select(self):
        # SELECT <select_list> <table_expression>
        self.token >> kw.SELECT
        select_list = self.select_list()
        self.table_expression()

    def select_list(self):
        #   <asterisk>
        # | <select_sublist> [ { <comma> <select_sublist> }... ]
        if self.token == ss.asterisk:
            data = self.token.next()
        else:
            data = [self.select_sublist()]
            while self.token == ss.comma:
                data.append(self.select_sublist())
        return data

    def select_sublist(self):
        #   <qualified_asterisk>
        # | <derived_column>
        # todo: Множества FIRST пересекаются
        knot = self.token.copy()
        is_crashed = logger.is_crashed
        try:
            data = self.qualified_asterisk()
        except FatalSyntaxException as ex1:
            self.token = knot.copy()
            try:
                data = self.derived_column()
            except FatalSyntaxException as ex2:
                self.token = knot
                raise FatalSyntaxException('Two ways with errors:\nEx1: {}\nEx2: {}'.format(ex1, ex2))
        # Восстановление состояне логгера
        logger.is_crashed = is_crashed
        return data

    def qualified_asterisk(self):
        # <asterisked_identifier_chain> <asterisk>
        data = self.asterisked_identifier_chain()
        self.token >> ss.asterisk
        return data

    def asterisked_identifier_chain(self):
        # <asterisked_identifier::ID> <period> [ { <asterisked_identifier> <period> }... ]
        data = [self.token >> tk.IdentifierToken]
        self.token >> ss.period
        while self.token == tk.IdentifierToken:
            data.append(self.token.next().decode)
            self.token >> ss.period
        return data

    def derived_column(self):
        # <value_expression> [ <as_clause> ]
        expression = self.value_expression()
        name = None
        if self.token == kw.AS:
            self.token.next()
            name = self.token >> tk.IdentifierToken
        elif self.token == tk.IdentifierToken:
            name = self.token.next()
        expression.as_(name)
        return expression

    def value_expression(self):
        #   <numeric_value_expression>
        # | <string_value_expression>
        # | <datetime_value_expression>
        # | <boolean_value_expression>
        # todo
        pass

    def numeric_value_expression(self):
        #   <term>
        # | <term> <plus_sign> <numeric_value_expression>
        # | <term> <minus_sign> <numeric_value_expression>
        left = self.term()
        if self.token == ss.plus_sign:
            self.token.next()
            cls = expr.AddNumericExpression
        elif self.token == ss.minus_sign:
            self.token.next()
            cls = expr.SubNumericExpression
        else:
            return left
        right = self.numeric_value_expression()
        return cls(left, right)

    def term(self):
        #   <factor>
        # | <factor> <asterisk> <term>
        # | <factor> <solidus> <term>
        left = self.factor()
        if self.token == ss.asterisk:
            self.token.next()
            cls = expr.MulNumericExpression
        elif self.token == ss.solidus:
            self.token.next()
            cls = expr.DivNumericExpression
        else:
            return left
        right = self.term()
        return cls(left, right)

    def factor(self):
        # [ <sign> ] <numeric_primary>
        sign = ss.plus_sign
        if self.token == (ss.plus_sign, ss.minus_sign):
            sign = self.sign()
        primary = self.numeric_primary()
        primary.set_sign(sign)
        return primary

    def numeric_primary(self):
        #   <value_expression_primary>
        return self.value_expression_primary()

    def string_value_expression(self):
        raise NotSupported

    def datetime_value_expression(self):
        raise NotSupported

    def boolean_value_expression(self):
        #   <boolean_term>
        # | <boolean_term> OR <boolean_value_expression>
        left = self.boolean_term()
        if self.token == kw.OR:
            right = self.boolean_value_expression()
            return expr.OrBooleanExpression(left, right)
        return left

    def boolean_term(self):
        #   <boolean_factor>
        # | <boolean_factor> AND <boolean_term>
        left = self.boolean_factor()
        if self.token == kw.AND:
            right = self.boolean_term()
            return expr.AndBooleanExpression(left, right)
        return left

    def boolean_factor(self):
        # [ NOT ] <boolean_test>
        is_not = True if self.token.optional >> kw.NOT else False
        factor = self.boolean_test()
        factor.set_not(is_not)
        return factor

    def boolean_test(self):
        # <boolean_primary> [ IS [ NOT ] <truth_value> ]
        primary = self.boolean_primary()
        if self.token == kw.IS:
            self.token.next()
            is_not = True if self.token.optional >> kw.NOT else False
            value = self.truth_value()
            primary = expr.IsBooleanExpression(primary, value, is_not)
        return primary

    def truth_value(self):
        #   TRUE
        # | FALSE
        # | NULL
        # В стандарте вместо NULL используют UNKNOWN
        return self.token >> (kw.TRUE, kw.FALSE, kw.NULL)

    def boolean_primary(self):
        #   <predicate>
        # | <parenthesized_boolean_value_expression>
        # | <nonparenthesized_value_expression_primary>
        pass

    def parenthesized_boolean_value_expression(self):
        # <left_paren> <boolean_value_expression> <right_paren>
        self.token >> ss.left_paren
        value = self.boolean_value_expression()
        self.token >> ss.right_arrow
        return value

    def value_expression_primary(self):
        #   <parenthesized_value_expression>
        # | <nonparenthesized_value_expression_primary>
        pass

    def parenthesized_value_expression(self):
        # <left_paren> <value_expression> <right_paren>
        pass

    def nonparenthesized_value_expression_primary(self):
        #   <unsigned_value_specification>
        # | <column_reference>
        pass

    def unsigned_value_specification(self):
        # <unsigned_literal>
        pass

    def literal(self):
        #   <signed_numeric_literal>
        # | <general_literal
        pass

    def signed_numeric_literal(self):
        # [ <sign> ] <unsigned_numeric_literal>
        pass

    def unsigned_literal(self):
        #   <unsigned_numeric_literal>
        # | <general_literal
        pass

    def unsigned_numeric_literal(self):
        #   INTEGER
        # | FLOAT
        pass

    def general_literal(self):
        #   <character_string_literal>
        # | <datetime_literal>
        # | <boolean_literal>
        pass

    def sign(self):
        #   <plus_sign>
        # | <minus_sign>
        return self.token >> (ss.plus_sign, ss.minus_sign)

    def column_reference(self):
        # <basic_identifier_chain>
        pass

    def basic_identifier_chain(self):
        # <identifier_chain>
        pass

    def identifier_chain(self):
        # <identifier::ID> [ { <period> <identifier::ID> }... ]
        pass

    def as_clause(self):
        # [ AS ] <column_name::ID>
        pass

    def table_expression(self):
        # <from_clause> [ <where_clause> ] [ <group_by_clause> ] [ <having_clause> ]
        pass

    def from_clause(self):
        # FROM <table_reference_list>
        pass

    def table_reference_list(self):
        # <table_reference> [ { <comma> <table_reference> }... ]
        pass

    def table_reference(self):
        #   <table_primary>
        # | <joined_table>
        pass

    def table_primary(self):
        # <table_name> [ AS ] <correlation_name::ID>
        pass

    def table_name(self):
        # <local_or_schema_qualified_name>
        pass

    def local_or_schema_qualified_name(self):
        # [ <local_or_schema_qualifier> <period> ] <qualified_identifier::ID>
        pass

    def local_or_schema_qualifier(self):
        # <schema_name>
        pass

    def schema_name(self):
        # [ <catalog_name::ID> <period> ] <unqualified_schema_name::ID>
        # Каталог - СУБД
        pass

    def joined_table(self):
        #   <cross_join>
        # | <qualified_join>
        # | <natural_join>
        # | <union_join>
        pass

    def cross_join(self):
        # <table_reference> CROSS JOIN <table_primary>
        pass

    def qualified_join(self):
        # <table_reference> [ <join_type> ] JOIN <table_reference> <join_specification>
        pass

    def natural_join(self):
        raise NotSupported

    def union_join(self):
        raise NotSupported

    def join_specification(self):
        #   <join_condition>
        # | <named_columns_join>
        pass

    def join_condition(self):
        # ON <search_condition>
        pass

    def named_columns_join(self):
        # USING <left_paren> <join_column_list> <right_paren>
        pass

    def join_type(self):
        #   INNER
        # | <outer_join_type> [ OUTER ]
        pass

    def outer_join_type(self):
        #   LEFT
        # | RIGHT
        # | FULL
        pass

    def join_column_list(self):
        # <column_name_list>
        pass

    def where_clause(self):
        # WHERE <search_condition>
        pass

    def group_by_clause(self):
        raise NotSupported

    def having_clause(self):
        raise NotSupported

    def insert(self):
        raise NotSupported

    def update(self):
        raise NotSupported

    def delete(self):
        raise NotSupported
