import logging
from itertools import product

from . import _logger
from . import dml
from . import expression as expr
from . import join as jn
from . import keywords as kw
from . import lexer
from . import parse_data
from . import predicates as ps
from . import structures as st
from . import symbols as ss
from . import token as tk
from .exceptions import NotSupported, FatalSyntaxException, SyntaxException

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

    def _choice_of_alternatives(self, alternatives):
        """
        Так как представленная грамматика не LL(1),
        то в затруднительных ситуациях используется
        выбор альтернатив при помощи отката

        (Альтернативы необходимо подавать в порядке
        уменьшения возможной длины разбора)
        """
        exceptions = []
        freeze_state = logger.is_crashed
        for idx, alt in enumerate(alternatives):
            knot = self.token.copy()
            try:
                data = (idx, alt())
                break
            except SyntaxException as ex:
                exceptions.append(ex)
                self.token = knot
        else:
            msg = 'Exceptions in all alternatives:\n{}'.format(
                '\n'.join(
                    '{}: {}'.format(alt.__name__, str(ex))
                    for alt, ex in zip(alternatives, exceptions)
                )
            )
            raise FatalSyntaxException(msg)
        logger.set_is_crashed(freeze_state)
        return data

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
        kwargs = self.table_expression()
        return dml.Selection(select_list=select_list, **kwargs)

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
        data = self._choice_of_alternatives([self.qualified_asterisk, self.derived_column])
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
        # | <boolean_value_expression>
        # | <string_value_expression>
        # | <datetime_value_expression>
        kind, value = self._choice_of_alternatives([self.numeric_primary, self.boolean_primary])
        return value

    def not_boolean_value_expression(self):
        #   <numeric_value_expression>
        # | <string_value_expression>
        # | <datetime_value_expression>
        kind, value = self._choice_of_alternatives([self.numeric_primary])
        return value

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
        # <value_expression_primary>
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
        if self.token == ss.left_paren:
            return self._choice_of_alternatives([self.parenthesized_value_expression, self.predicate])
        return self.nonparenthesized_value_expression_primary()

    def predicate(self):
        # <comparison_predicate>
        return self.comparison_predicate()

    def comparison_predicate(self):
        # <operand_comparison> <comp_op> <operand_comparison>
        left = self.operand_comparison()
        op = self.comp_op()
        right = self.operand_comparison()
        return ps.ComparisonPredicate(left, right, op)

    def operand_comparison(self):
        if self.token == ss.left_paren:
            return self.parenthesized_value_expression()
        return self.not_boolean_value_expression()

    def comp_op(self):
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

    def row_value_expression(self):
        # <row_value_special_case>
        return self.row_value_special_case()

    def row_value_special_case(self):
        #   <value_expression>
        # | <value_specification>
        return self._choice_of_alternatives([self.value_expression, self.value_specification])

    def value_specification(self):
        # <literal>
        return self.literal()

    def parenthesized_boolean_value_expression(self):
        # <left_paren> <boolean_value_expression> <right_paren>
        self.token >> ss.left_paren
        value = self.boolean_value_expression()
        self.token >> ss.right_arrow
        return value

    def value_expression_primary(self):
        #   <parenthesized_value_expression>
        # | <nonparenthesized_value_expression_primary>
        if self.token == ss.left_paren:
            return self.parenthesized_value_expression()
        return self.nonparenthesized_value_expression_primary()

    def parenthesized_value_expression(self):
        # <left_paren> <value_expression> <right_paren>
        self.token >> ss.left_paren
        data = self.value_expression()
        self.token >> ss.right_paren
        return data

    def nonparenthesized_value_expression_primary(self):
        #   <unsigned_value_specification>
        # | <column_reference>
        if self.token == tk.IdentifierToken:
            return self.column_reference()
        return self.unsigned_value_specification()

    def unsigned_value_specification(self):
        # <unsigned_literal>
        return self.unsigned_literal()

    def literal(self):
        #   <signed_numeric_literal>
        # | <general_literal>
        if self.token == (tk.IntToken, tk.FloatToken, ss.plus_sign, ss.plus_sign):
            return self.signed_numeric_literal()
        return self.general_literal()

    def signed_numeric_literal(self):
        # [ <sign> ] <unsigned_numeric_literal>
        sign = ss.plus_sign
        if self.token == (ss.plus_sign, ss.minus_sign):
            sign = self.sign()
        value = self.unsigned_numeric_literal()
        if sign == ss.minus_sign:
            value *= -1
        return value

    def unsigned_literal(self):
        #   <unsigned_numeric_literal>
        # | <general_literal
        if self.token == [tk.IntToken, tk.FloatToken]:
            return self.unsigned_numeric_literal()
        return self.general_literal()

    def unsigned_numeric_literal(self):
        #   INTEGER
        # | FLOAT
        return self.token >> (tk.IntToken, tk.FloatToken)

    def general_literal(self):
        #   <character_string_literal::STR>
        # | <datetime_literal::DT>
        # | <boolean_literal>
        if self.token.optional >> kw.TRUE:
            return True
        elif self.token.optional >> kw.FALSE:
            return False
        elif self.token.optional >> kw.NULL:
            return None
        return self.token >> (tk.StringToken, tk.DateToken, tk.DatetimeToken)

    def sign(self):
        #   <plus_sign>
        # | <minus_sign>
        return self.token >> (ss.plus_sign, ss.minus_sign)

    def column_reference(self):
        # <basic_identifier_chain>
        return self.basic_identifier_chain()

    def basic_identifier_chain(self):
        # <identifier_chain>
        return self.identifier_chain()

    def identifier_chain(self):
        # <identifier::ID> [ { <period> <identifier::ID> }... ]
        chain = st.NameChain(self.token >> tk.IdentifierToken)
        while self.token.optional >> ss.period:
            chain.push_last(self.token >> tk.IdentifierToken)
        return chain

    def as_clause(self):
        # [ AS ] <column_name::ID>
        _ = self.token.optional >> kw.AS
        return self.token >> tk.IdentifierToken

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

    def from_clause(self):
        # FROM <table_reference_list>
        self.token >> kw.FROM
        return self.table_reference_list()

    def table_reference_list(self):
        # <table_reference> [ { <comma> <table_reference> }... ]
        data = [self.table_reference()]
        while self.token.optional >> ss.comma:
            data.append(self.table_reference())
        return data

    def table_reference(self):
        # <join_factor> [ { <join_type> }... ]
        first = self.join_factor()
        joins = []
        while self.token == (kw.CROSS, kw.JOIN, kw.INNER, kw.LEFT, kw.RIGHT, kw.FULL):
            joins.append(self.joined_table())

        accumulate = first
        for join in joins:
            accumulate = join.set_left(accumulate)

        return accumulate

    def join_factor(self):
        #   <table_primary>
        # | <left_paren> <table_reference> <right_paren>
        if self.token.optional >> ss.left_paren:
            data = self.table_reference()
            self.token >> ss.right_paren
        else:
            data = self.table_primary()
        return data

    def table_primary(self):
        # <table_or_query_name> [ [ AS ] <correlation_name::ID> ]
        name = self.table_or_query_name()
        if self.token.optional >> kw.AS:
            name.as_(self.token >> tk.IdentifierToken)
        else:
            name.as_(self.token.optional >> tk.IdentifierToken)
        return name

    def table_or_query_name(self):
        #   <table_name>
        # | <query_name>
        return self.table_name()

    def table_name(self):
        return self.local_or_schema_qualifier()

    def local_or_schema_qualified_name(self):
        # [ <local_or_schema_qualifier> <period> ] <qualified_identifier::ID>
        name = self.local_or_schema_qualifier()
        if self.token.optional >> ss.period:
            name.push_last(self.token >> tk.IdentifierToken)
        return name

    def local_or_schema_qualifier(self):
        # <schema_name>
        return self.schema_name()

    def schema_name(self):
        # [ <catalog_name::ID> <period> ] <unqualified_schema_name::ID>
        # Каталог - СУБД
        first_name = self.token >> tk.IdentifierToken
        if self.token.optional >> ss.period:
            second_name = self.token >> tk.IdentifierToken
            name = st.NameChain(first_name, second_name)
        else:
            name = st.NameChain(first_name)
        return name

    def joined_table(self):
        if self.token == kw.CROSS:
            join = self.cross_join()
        else:
            join = self.qualified_join()
        return join

    def cross_join(self):
        # CROSS JOIN <join_factor>
        self.token >> kw.CROSS
        self.token >> kw.JOIN
        return jn.CrossJoin(self.join_factor())

    def qualified_join(self):
        # [ <join_type> ] JOIN <join_factor> <join_specification>
        cls = jn.DEFAULT_JOIN
        if self.token == (kw.INNER, kw.LEFT, kw.RIGHT, kw.FULL):
            cls = self.join_type()
        self.token >> kw.JOIN
        right = self.join_factor()
        spec = self.join_specification()
        return cls(right, spec)

    def natural_join(self):
        raise NotSupported

    def union_join(self):
        raise NotSupported

    def join_specification(self):
        #   <join_condition>
        # | <named_columns_join>
        if self.token == kw.ON:
            data = self.join_condition()
        else:
            data = self.named_columns_join()
        return data

    def join_condition(self):
        # ON <search_condition>
        self.token >> kw.ON
        return self.search_condition()

    def search_condition(self):
        return self.boolean_value_expression()

    def named_columns_join(self):
        # USING <left_paren> <join_column_list> <right_paren>
        self.token >> kw.USING
        self.token >> ss.left_paren
        data = self.join_column_list()
        self.token >> ss.right_paren
        return data

    def join_type(self):
        #   INNER
        # | <outer_join_type> [ OUTER ]
        if self.token == (kw.LEFT, kw.RIGHT, kw.FULL):
            cls = self.outer_join_type()
            _ = self.token.optional >> kw.OUTER
            return cls
        self.token >> kw.INNER
        return jn.InnerJoin

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

    def join_column_list(self):
        # <column_name_list>
        return self.column_name_list()

    def column_name_list(self):
        # <column_name::ID> [ { <comma> <column_name::ID> }... ]
        data = [self.token >> tk.IdentifierToken]
        while self.token.optional >> ss.comma:
            data.append(self.token >> tk.IdentifierToken)
        return data

    def where_clause(self):
        # WHERE <search_condition>
        self.token >> kw.WHERE
        return self.search_condition()

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