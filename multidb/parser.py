import logging
from itertools import product

from . import _logger
from . import data_types as dt
from . import dml
from . import expression as expr
from . import join as jn
from . import keywords as kw
from . import lexer
from . import parse_data
from . import symbols as ss
from . import token as tk
from . import utils
from .exceptions import NotSupported, FatalSyntaxException, SyntaxException

# noinspection PyTypeChecker
logger = logging.getLogger('parser')  # type: _logger.ParserLogger
logger.display_position()
# noinspection PyTypeChecker
tree_logger = logging.getLogger('tree')  # type: _logger.ParserLogger
tree_logger.display_position()


class CmpLexer(lexer.Lexer):
    STRICT = 0
    SAFE = 1
    OPTIONAL = 2

    def __init__(self, pos, interval=lexer.EMPTY_INTERVAL, last_interval=lexer.EMPTY_INTERVAL, current_tokens=None):
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
        return fail, value, other

    def __rshift__(self, other):
        fail, value, other = self.check(other)
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
    @classmethod
    def build(cls, program):
        lex = CmpLexer(lexer.Position(program))
        return cls(lex)

    def __init__(self, lex: CmpLexer):
        logger.set_parser(self)
        self.token = lex
        self.data = parse_data.ParseData()

    def _choice_of_alternatives(self, alternatives):
        """
        Так как представленная грамматика не LL(1),
        то в затруднительных ситуациях используется
        выбор альтернатив при помощи отката
        """
        exceptions = []
        success = []
        freeze_state = logger.is_crashed
        for idx, alt in enumerate(alternatives):
            logger.append_line_buffer()
            knot = self.token.copy()
            try:
                data = (idx, alt())
                success.append((data, logger.buffer.pop(), self.token.copy()))
            except SyntaxException as ex:
                exceptions.append(ex)
                logger.pop_line_buffer()
            self.token = knot
        if not success:
            msg = 'Exceptions in all alternatives:\n{}'.format(
                '\n'.join(
                    '{}: {}'.format(alt.__name__, str(ex))
                    for alt, ex in zip(alternatives, exceptions)
                )
            )
            raise FatalSyntaxException(msg)

        # Выбирается альтернатива с наибольшей длиной
        # Если таких нексколько, то выбирается с минимальным индексом
        data, buff, token = max(success, key=lambda x: (x[-1].pos.idx, -x[0][0]))
        self.token = token

        logger.append_line_buffer(buff)
        logger.pop_line_buffer(True)
        logger.set_is_crashed(freeze_state)
        return data


class SQLParser(Parser):

    def __init__(self, lex: CmpLexer):
        super().__init__(lex)
        self.cc = None

    def set_cc(self, cc):
        self.cc = cc

    def program(self):
        #   <select>
        # | <insert>
        # | <update>
        # | <delete>
        self.token.next()

        data = None
        if self.token == kw.SELECT:
            data = self.select()

        elif self.token == kw.INSERT:
            data = self.insert()

        elif self.token == kw.UPDATE:
            data = self.update()

        elif self.token == kw.DELETE:
            data = self.delete()
        _ = self.token.optional >> ss.semicolon
        self.token >> tk.EndToken
        return data

    @utils.log(tree_logger)
    def select(self):
        # SELECT <select_list> <table_expression>
        self.token >> kw.SELECT
        select_list = self.select_list()
        kwargs = self.table_expression()
        # Todo
        return dml.Select(self.cc, select_list=select_list, **kwargs)

    @utils.log(tree_logger)
    def select_list(self):
        #   <asterisk>
        # | <select_sublist> [ { <comma> <select_sublist> }... ]
        if self.token == ss.asterisk:
            data = self.token.next()
        else:
            data = [self.select_sublist()]
            while self.token.optional >> ss.comma:
                data.append(self.select_sublist())
        return data

    @utils.log(tree_logger)
    def select_sublist(self):
        #   <qualified_asterisk>
        # | <derived_column>
        alt, data = self._choice_of_alternatives([self.qualified_asterisk, self.derived_column])
        is_qualified_asterisk = alt == 0
        return is_qualified_asterisk, data

    @utils.log(tree_logger)
    def qualified_asterisk(self):
        # <asterisked_identifier_chain> <asterisk>
        data = self.asterisked_identifier_chain()
        self.token >> ss.asterisk
        return data

    @utils.log(tree_logger)
    def asterisked_identifier_chain(self):
        # <asterisked_identifier::ID> <period> [ { <asterisked_identifier> <period> }... ]
        data = [self.token >> tk.IdentifierToken]
        self.token >> ss.period
        while True:
            el = self.token.optional >> tk.IdentifierToken
            if not el:
                break
            data.append(el)
            self.token >> ss.period
        return utils.NamingChain(*data)

    @utils.log(tree_logger)
    def derived_column(self):
        # <value_expression> [ [ AS ] <column_name::ID> ]
        expression = self.value_expression()
        name = None
        if self.token == kw.AS:
            self.token.next()
            name = self.token >> tk.IdentifierToken
        elif self.token == tk.IdentifierToken:
            name = self.token.next()
        expression.as_(name)
        return expression

    @utils.log(tree_logger)
    def value_expression(self):
        #   <numeric_value_expression>
        # | <boolean_value_expression>
        # | <string_value_expression>
        # | <datetime_value_expression>
        kind, value = self._choice_of_alternatives([
            self.numeric_value_expression,
            self.boolean_value_expression
        ])
        return value

    @utils.log(tree_logger)
    def not_boolean_value_expression(self):
        #   <numeric_value_expression>
        # | <string_value_expression>
        # | <datetime_value_expression>
        kind, value = self._choice_of_alternatives([self.numeric_value_expression])
        return value

    @utils.log(tree_logger)
    def numeric_value_expression(self):
        #   <term>
        # | <term> <plus_sign> <numeric_value_expression>
        # | <term> <minus_sign> <numeric_value_expression>
        left = self.term()
        if self.token == ss.plus_sign:
            self.token.next()
            cls = expr.Add
        elif self.token == ss.minus_sign:
            self.token.next()
            cls = expr.Sub
        else:
            return left
        right = self.numeric_value_expression()
        return cls(left, right)

    @utils.log(tree_logger)
    def term(self):
        #   <factor>
        # | <factor> <asterisk> <term>
        # | <factor> <solidus> <term>
        left = self.factor()
        if self.token == ss.asterisk:
            self.token.next()
            cls = expr.Mul
        elif self.token == ss.solidus:
            self.token.next()
            cls = expr.Div
        else:
            return left
        right = self.term()
        return cls(left, right)

    @utils.log(tree_logger)
    def factor(self):
        # [ <minus_sign> ] <numeric_primary>
        sign = self.token.optional >> ss.minus_sign
        if self.token == (ss.plus_sign, ss.minus_sign):
            sign = self.sign()
        primary = self.numeric_primary()
        if sign is not None:
            primary = expr.UnarySign(primary, sign)
        return primary

    @utils.log(tree_logger)
    def numeric_primary(self):
        # <value_expression_primary>
        return self.value_expression_primary()

    @utils.log(tree_logger)
    def string_value_expression(self):
        raise NotSupported

    @utils.log(tree_logger)
    def datetime_value_expression(self):
        raise NotSupported

    @utils.log(tree_logger)
    def boolean_value_expression(self):
        #   <boolean_term>
        # | <boolean_term> OR <boolean_value_expression>
        left = self.boolean_term()
        if self.token.optional >> kw.OR:
            right = self.boolean_value_expression()
            return expr.Or(left, right)
        return left

    @utils.log(tree_logger)
    def boolean_term(self):
        #   <boolean_factor>
        # | <boolean_factor> AND <boolean_term>
        left = self.boolean_factor()
        if self.token.optional >> kw.AND:
            right = self.boolean_term()
            return expr.And(left, right)
        return left

    @utils.log(tree_logger)
    def boolean_factor(self) -> dt.BooleanTest:
        # [ NOT ] <boolean_test>
        is_not = True if self.token.optional >> kw.NOT else False
        factor = self.boolean_test()
        if is_not:
            factor = expr.Not(factor)
        return factor

    @utils.log(tree_logger)
    def boolean_test(self) -> dt.BooleanTest:
        # <boolean_primary> [ IS [ NOT ] <truth_value> ]
        primary = self.boolean_primary()
        if self.token.optional >> kw.IS:
            is_not = True if self.token.optional >> kw.NOT else False
            value = self.truth_value()
            primary = expr.Is(primary, value)
            if is_not:
                primary = expr.Not(primary)
        return primary

    @utils.log(tree_logger)
    def truth_value(self) -> dt.TruthValue:
        #   TRUE
        # | FALSE
        # | NULL
        # В стандарте вместо NULL используют UNKNOWN
        value = self.token >> (kw.TRUE, kw.FALSE, kw.NULL)
        if value == kw.TRUE:
            return True
        elif value == kw.FALSE:
            return False
        return None

    @utils.log(tree_logger)
    def boolean_primary(self) -> dt.BooleanPrimary:
        #   <predicate>
        # | <parenthesized_value_expression>
        # | <nonparenthesized_value_expression_primary>
        # Todo: parenthesized_value_expression вместо parenthesized_boolean_value_expression
        alt, value = self._choice_of_alternatives([
            self.predicate,
            self.parenthesized_value_expression,
            self.nonparenthesized_value_expression_primary,
        ])
        return value

    @utils.log(tree_logger)
    def predicate(self) -> dt.ComparisonPredicate:
        # <comparison_predicate>
        return self.comparison_predicate()

    @utils.log(tree_logger)
    def comparison_predicate(self) -> dt.ComparisonPredicate:
        # <operand_comparison> <comp_op> <operand_comparison>
        left = self.operand_comparison()
        op = self.comp_op()
        right = self.operand_comparison()
        return expr.ComparisonPredicate(left, right, op)

    @utils.log(tree_logger)
    def operand_comparison(self) -> dt.ValueExpression:
        if self.token == ss.left_paren:
            return self.parenthesized_value_expression()
        return self.not_boolean_value_expression()

    @utils.log(tree_logger)
    def comp_op(self) -> str:
        #   <equals_operator>
        # | <not_equals_operator>
        # | <less_than_operator>
        # | <greater_than_operator>
        # | <less_than_or_equals_operator>
        # | <greater_than_or_equals_operator>
        return self.token >> (
            ss.equals_operator, ss.not_equals_operator,
            ss.less_than_operator, ss.greater_than_operator,
            ss.less_than_or_equals_operator, ss.greater_than_or_equals_operator
        )

    @utils.log(tree_logger)
    def row_value_expression(self) -> dt.RowValueSpecialCase:
        # <row_value_special_case>
        return self.row_value_special_case()

    @utils.log(tree_logger)
    def row_value_special_case(self) -> dt.RowValueSpecialCase:
        #   <value_expression>
        # | <value_specification>
        alt, value = self._choice_of_alternatives([self.value_expression, self.value_specification])
        return value

    @utils.log(tree_logger)
    def value_specification(self) -> dt.Literal:
        # <literal>
        return self.literal()

    # @utils.log(tree_logger)
    # def parenthesized_boolean_value_expression(self) -> dt.BooleanValueExpression:
    #     # <left_paren> <boolean_value_expression> <right_paren>
    #     self.token >> ss.left_paren
    #     value = self.boolean_value_expression()
    #     self.token >> ss.right_paren
    #     return value

    @utils.log(tree_logger)
    def value_expression_primary(self) -> dt.ValueExpressionPrimary:
        #   <parenthesized_value_expression>
        # | <nonparenthesized_value_expression_primary>
        if self.token == ss.left_paren:
            return self.parenthesized_value_expression()
        return self.nonparenthesized_value_expression_primary()

    @utils.log(tree_logger)
    def parenthesized_value_expression(self) -> dt.ValueExpression:
        # <left_paren> <value_expression> <right_paren>
        self.token >> ss.left_paren
        data = self.value_expression()
        self.token >> ss.right_paren
        return data

    @utils.log(tree_logger)
    def nonparenthesized_value_expression_primary(self) -> dt.NonparenthesizedValueExpressionPrimary:
        #   <unsigned_value_specification>
        # | <column_reference>
        if self.token == tk.IdentifierToken:
            return expr.Column(self.column_reference())
        else:
            return self.unsigned_value_specification()

    @utils.log(tree_logger)
    def unsigned_value_specification(self) -> dt.UnsignedLiteral:
        # <unsigned_literal>
        return self.unsigned_literal()

    @utils.log(tree_logger)
    def literal(self) -> dt.Literal:
        #   <signed_numeric_literal>
        # | <general_literal>
        if self.token == (tk.IntToken, tk.FloatToken, ss.plus_sign, ss.plus_sign):
            return self.signed_numeric_literal()
        return self.general_literal()

    @utils.log(tree_logger)
    def signed_numeric_literal(self) -> dt.SignedNumericLiteral:
        # [ <sign> ] <unsigned_numeric_literal>
        sign = ss.plus_sign
        if self.token == (ss.plus_sign, ss.minus_sign):
            sign = self.sign()
        value = self.unsigned_numeric_literal()
        if sign is not None:
            value = expr.UnarySign(value, sign)
        return value

    @utils.log(tree_logger)
    def unsigned_literal(self) -> dt.UnsignedLiteral:
        #   <unsigned_numeric_literal>
        # | <general_literal
        if self.token == (tk.IntToken, tk.FloatToken):
            return self.unsigned_numeric_literal()
        return self.general_literal()

    @utils.log(tree_logger)
    def unsigned_numeric_literal(self) -> dt.UnsignedNumericLiteral:
        #   INTEGER
        # | FLOAT
        value = self.token >> (tk.FloatToken, tk.IntToken)
        return expr.PrimaryValue.auto(value)

    @utils.log(tree_logger)
    def general_literal(self) -> dt.GeneralLiteral:
        #   <character_string_literal::STR>
        # | <datetime_literal::DT>
        # | <boolean_literal>
        value = self.token >> (kw.TRUE, kw.FALSE, kw.NULL, tk.StringToken, tk.DatetimeToken, tk.DateToken)
        if value == kw.TRUE:
            return expr.Bool(True)
        elif value == kw.FALSE:
            return expr.Bool(False)
        elif value == kw.NULL:
            return expr.Null()
        return expr.PrimaryValue.auto(value)

    @utils.log(tree_logger)
    def sign(self) -> str:
        #   <plus_sign>
        # | <minus_sign>
        return self.token >> (ss.plus_sign, ss.minus_sign)

    @utils.log(tree_logger)
    def column_reference(self) -> dt.IdentifierChain:
        # <basic_identifier_chain>
        return self.basic_identifier_chain()

    @utils.log(tree_logger)
    def basic_identifier_chain(self) -> dt.IdentifierChain:
        # <identifier_chain>
        return self.identifier_chain()

    @utils.log(tree_logger)
    def identifier_chain(self) -> dt.IdentifierChain:
        # <identifier::ID> [ { <period> <identifier::ID> }... ]
        chain = utils.NamingChain(self.token >> tk.IdentifierToken)
        while self.token.optional >> ss.period:
            chain.push_last(self.token >> tk.IdentifierToken)
        return chain

    @utils.log(tree_logger)
    def table_expression(self):
        # <from_clause> [ <where_clause> ] [ <group_by_clause> ] [ <having_clause> ]
        data = {'from_': self.from_clause()}

        if self.token == kw.WHERE:
            data['where'] = self.where_clause()
        if self.token == kw.GROUP:
            data['group'] = self.group_by_clause()
        if self.token == kw.HAVING:
            data['having'] = self.having_clause()

        return data

    @utils.log(tree_logger)
    def from_clause(self):
        # FROM <table_reference_list>
        self.token >> kw.FROM
        return self.table_reference_list()

    @utils.log(tree_logger)
    def table_reference_list(self):
        # <table_reference> [ { <comma> <table_reference> }... ]
        data = [self.table_reference()]
        while self.token.optional >> ss.comma:
            data.append(self.table_reference())
        return data

    @utils.log(tree_logger)
    def table_reference(self):
        # <join_factor> [ { <join_type> }... ]
        first = self.join_factor()
        joins = []
        while self.token == (kw.CROSS, kw.JOIN, kw.INNER, kw.LEFT, kw.RIGHT, kw.FULL):
            joins.append(self.joined_table())

        accumulate = first
        for join in joins:
            join.set_left(accumulate)
            accumulate = join

        return accumulate

    @utils.log(tree_logger)
    def join_factor(self):
        #   <table_primary>
        # | <left_paren> <table_reference> <right_paren>
        if self.token.optional >> ss.left_paren:
            data = self.table_reference()
            self.token >> ss.right_paren
        else:
            data = self.table_primary()
        return data

    @utils.log(tree_logger)
    def table_primary(self):
        # <table_or_query_name> [ [ AS ] <correlation_name::ID> ]
        name = self.table_or_query_name()
        if self.token.optional >> kw.AS:
            name.as_(self.token >> tk.IdentifierToken)
        else:
            name.as_(self.token.optional >> tk.IdentifierToken)
        return name

    @utils.log(tree_logger)
    def table_or_query_name(self):
        #   <table_name>
        # | <query_name>
        return self.table_name()

    @utils.log(tree_logger)
    def table_name(self):
        # <basic_identifier_chain>
        return self.basic_identifier_chain()

    @utils.log(tree_logger)
    def joined_table(self):
        #   <cross_join>
        # | <qualified_join>
        if self.token == kw.CROSS:
            join = self.cross_join()
        else:
            join = self.qualified_join()
        return join

    @utils.log(tree_logger)
    def cross_join(self):
        # CROSS JOIN <join_factor>
        self.token >> kw.CROSS
        self.token >> kw.JOIN
        return jn.CrossJoin(None, self.join_factor())

    @utils.log(tree_logger)
    def qualified_join(self):
        # [ <join_type> ] JOIN <join_factor> <join_specification>
        cls = jn.DEFAULT_JOIN
        if self.token == (kw.INNER, kw.LEFT, kw.RIGHT, kw.FULL):
            cls = self.join_type()
        self.token >> kw.JOIN
        right = self.join_factor()
        spec = self.join_specification()
        return cls(None, right, spec)

    @utils.log(tree_logger)
    def natural_join(self):
        raise NotSupported

    @utils.log(tree_logger)
    def union_join(self):
        raise NotSupported

    # @utils.log(tree_logger)
    # def join_specification(self):
    #     #   <join_condition>
    #     # | <named_columns_join>
    #     if self.token == kw.ON:
    #         data = self.join_condition()
    #     else:
    #         data = self.named_columns_join()
    #     return data

    @utils.log(tree_logger)
    def join_specification(self):
        # <join_condition>
        return self.join_condition()

    @utils.log(tree_logger)
    def join_condition(self):
        # ON <search_condition>
        self.token >> kw.ON
        return self.search_condition()

    @utils.log(tree_logger)
    def search_condition(self):
        return self.boolean_value_expression()

    # @utils.log(tree_logger)
    # def named_columns_join(self):
    #     # USING <left_paren> <join_column_list> <right_paren>
    #     self.token >> kw.USING
    #     self.token >> ss.left_paren
    #     data = self.join_column_list()
    #     self.token >> ss.right_paren
    #     return data

    @utils.log(tree_logger)
    def join_type(self):
        #   INNER
        # | <outer_join_type> [ OUTER ]
        if self.token == (kw.LEFT, kw.RIGHT, kw.FULL):
            cls = self.outer_join_type()
            _ = self.token.optional >> kw.OUTER
            return cls
        self.token >> kw.INNER
        return jn.InnerJoin

    @utils.log(tree_logger)
    def outer_join_type(self):
        #   LEFT
        # | RIGHT
        # | FULL
        if self.token.optional >> kw.LEFT:
            return jn.LeftJoin
        elif self.token.optional >> kw.RIGHT:
            return jn.RightJoin
        self.token >> kw.FULL
        return jn.FullJoin

    @utils.log(tree_logger)
    def join_column_list(self):
        # <column_name_list>
        return self.column_name_list()

    @utils.log(tree_logger)
    def column_name_list(self):
        # <column_name::ID> [ { <comma> <column_name::ID> }... ]
        data = [self.token >> tk.IdentifierToken]
        while self.token.optional >> ss.comma:
            data.append(self.token >> tk.IdentifierToken)
        return data

    @utils.log(tree_logger)
    def where_clause(self):
        # WHERE <search_condition>
        self.token >> kw.WHERE
        return self.search_condition()

    @utils.log(tree_logger)
    def group_by_clause(self):
        raise NotSupported

    @utils.log(tree_logger)
    def having_clause(self):
        raise NotSupported

    @utils.log(tree_logger)
    def insert(self):
        raise NotSupported

    @utils.log(tree_logger)
    def update(self):
        raise NotSupported

    @utils.log(tree_logger)
    def delete(self):
        raise NotSupported


class PSQLCmpLexer(CmpLexer):
    TOKENS = [
        tk.IntToken,
        tk.FloatToken,
        tk.StringToken,
        tk.DateToken,
        tk.DatetimeToken,
        tk.PSQLIdentifierToken,
        tk.KeywordToken,
        tk.SymbolToken
    ]


class IndexParser(Parser):

    @classmethod
    def build(cls, program):
        lex = PSQLCmpLexer(lexer.Position(program))
        return cls(lex)

    def program(self):
        self.token.next()
        self.token >> kw.CREATE
        is_unique = self.token.optional >> kw.UNIQUE
        self.token >> kw.INDEX
        if self.token.optional >> kw.IF:
            self.token >> kw.NOT
            self.token >> kw.EXISTS
            _ = self.token >> tk.PSQLIdentifierToken  # name
        else:
            _ = self.token.optional >> tk.PSQLIdentifierToken  # name
        self.token >> kw.ON
        _ = self.token.optional >> kw.ONLY  # is_only
        _ = self.naming_chain()  # table_name

        method = self.token.optional >> kw.USING
        if method:
            method = self.token >> [kw.BTREE, kw.HASH, kw.GIST, kw.SPGIST, kw.GIN, kw.BRIN]

        self.token >> ss.left_paren
        columns = self.columns()
        self.token >> ss.right_paren

        '''
        include = self.token.optional >> kw.INCLUDE
        if include:
            self.token >> ss.left_paren
            include = self.column_list()
            self.token >> ss.right_paren

        storage_parameters = self.token.optional >> kw.WITH
        if storage_parameters:
            self.token >> ss.left_paren
            storage_parameters = self.storage_parameters()
            self.token >> ss.right_paren

        table_space = self.token.optional >> kw.TABLESPACE
        if table_space:
            table_space = self.token >> tk.IdentifierToken

        predicate = self.token.optional >> kw.WHERE
        if predicate:
            predicate = self.predicate()
        '''
        return columns, bool(is_unique), method

    def column_list(self):
        data = [self.token >> tk.PSQLIdentifierToken]
        while self.token.optional >> ss.comma:
            data.append(self.token >> tk.PSQLIdentifierToken)
        return data

    def columns(self):
        data = [self.column()]
        while self.token.optional >> ss.comma:
            data.append(self.column())
        return data

    def column(self):
        if self.token.optional >> ss.left_paren:
            column = self.expression()
            self.token >> ss.right_paren
        else:
            column = self.token >> tk.PSQLIdentifierToken

        collate = self.token.optional >> kw.COLLATE
        if collate:
            collate = self.token >> tk.PSQLIdentifierToken

        opclass = self.token.optional >> tk.PSQLIdentifierToken
        asc_desc = self.token.optional >> (kw.ASC, kw.DESC)
        nulls = self.token.optional >> kw.NULLS
        if nulls:
            nulls = self.token >> [kw.FIRST, kw.LAST]

        return column, collate, opclass, asc_desc, nulls

    def naming_chain(self) -> dt.IdentifierChain:
        # <identifier::ID> [ { <period> <identifier::ID> }... ]
        chain = utils.NamingChain(self.token >> tk.PSQLIdentifierToken)
        while self.token.optional >> ss.period:
            chain.push_last(self.token >> tk.PSQLIdentifierToken)
        return chain

    def storage_parameters(self):
        data = [self.storage_parameter()]
        if self.token.optional >> ss.comma:
            data.append(self.storage_parameter())
        return data

    def storage_parameter(self):
        key = self.token >> tk.PSQLIdentifierToken
        self.token >> ss.equals_operator
        value = self.token >> tk.PSQLIdentifierToken
        return key, value

    def expression(self):
        raise NotImplementedError

    def predicate(self):
        raise NotImplementedError
