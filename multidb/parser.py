import logging

from . import _logger
from .exceptions import NotSupported

# noinspection PyTypeChecker
logger = logging.getLogger('parser')  # type: _logger.ParserLogger


class Parser:
    def __init__(self, lex):
        self.token = lex

    def program(self):
        #   <select>
        # | <insert>
        # | <update>
        # | <delete>
        pass

    def select(self):
        # SELECT <select_list> <table_expression>
        pass

    def selection_list(self):
        #   <asterisk>
        # | <select sublist> [ { <comma> <select sublist> }... ]
        pass

    def select_sublist(self):
        # <derived_column>
        pass

    def derived_column(self):
        # <value_expression> [ <as_clause> ]
        pass

    def value_expression(self):
        #   <numeric_value_expression>
        # | <string_value_expression>
        # | <datetime_value_expression>
        # | <boolean_value_expression>
        pass

    def numeric_value_expression(self):
        #   <term>
        # | <numeric_value_expression> <plus_sign> <term>
        # | <numeric_value_expression> <minus_sign> <term>
        pass

    def term(self):
        #   <factor>
        # | <term> <asterisk> <factor>
        # | <term> <solidus> <factor>
        pass

    def factor(self):
        # [ <sign> ] <numeric primary>
        pass

    def numeric_primary(self):
        #   <value_expression_primary>
        # | <numeric_value_function>
        pass

    def string_value_expression(self):
        raise NotSupported

    def datetime_value_expression(self):
        raise NotSupported

    def boolean_value_expression(self):
        #   <boolean_term>
        # | <boolean_value_expression> OR <boolean_term>
        pass

    def boolean_term(self):
        #   <boolean_factor>
        # | <boolean_term> AND <boolean_factor>
        pass

    def boolean_factor(self):
        # [ NOT ] <boolean_test>
        pass

    def boolean_test(self):
        # <boolean_primary> [ IS [ NOT ] <truth_value> ]
        pass

    def truth_value(self):
        #   TRUE
        # | FALSE
        # | NULL
        # В стандарте вместо NULL используют UNKNOWN
        pass

    def boolean_primary(self):
        #   <predicate>
        # | <parenthesized_boolean_value_expression>
        # | <nonparenthesized_value_expression_primary>
        pass

    def parenthesized_boolean_value_expression(self):
        # <left_paren> <boolean_value_expression> <right_paren>
        pass

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
        pass

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
