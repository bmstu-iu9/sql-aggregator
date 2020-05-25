import logging
from datetime import date, datetime
from itertools import combinations_with_replacement
from typing import Union

from . import mixins as mx
from . import symbols as ss
from . import utils


class BaseExpression(mx.AsMixin):
    @property
    def convolution(self):
        return self

    @property
    def to_int(self):
        return self

    @property
    def to_bool(self):
        return self


class PrimaryValue(BaseExpression):
    INT = 0
    FLOAT = 1
    STR = 2
    DATE = 3
    DATETIME = 4
    BOOL = 5
    NULL = 6
    COLUMN = 7

    KIND = None

    @classmethod
    def auto(cls, value):
        if isinstance(value, int):
            return Int(value)
        elif isinstance(value, float):
            return Float(value)
        elif isinstance(value, str):
            return Str(value)
        elif isinstance(value, datetime):
            return Datetime(value)
        elif isinstance(value, date):
            return Date(value)
        elif isinstance(value, bool):
            return Bool(value)
        elif value is None:
            return Null()
        elif isinstance(value, utils.NamingChain):
            return Column(value)
        raise ValueError('Invalid data type: {}({})'.format(type(value), value))

    def __init__(self, value, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.value = value

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, self.value)


class PrimaryNumeric(PrimaryValue):
    @property
    def to_bool(self):
        return Bool(bool(self.value))


class Int(PrimaryNumeric):
    KIND = PrimaryValue.INT


class Float(PrimaryNumeric):
    KIND = PrimaryValue.FLOAT


class Str(PrimaryValue):
    # Todo: Does not work
    KIND = PrimaryValue.STR


class Date(PrimaryValue):
    # Todo: Does not work
    KIND = PrimaryValue.DATE


class Datetime(PrimaryValue):
    # Todo: Does not work
    KIND = PrimaryValue.DATETIME


class Bool(PrimaryValue):
    KIND = PrimaryValue.BOOL

    @property
    def to_int(self):
        return Int(int(self.value))


class Null(PrimaryValue):
    KIND = PrimaryValue.NULL

    def __init__(self, value=None, *args, **kwargs):
        super().__init__(value, *args, **kwargs)


class Column(PrimaryValue):
    KIND = PrimaryValue.COLUMN


class SimpleExpression(BaseExpression):
    logger = logging.getLogger('simple_expression')

    def __init__(self, expr, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.expr = expr


class NumericExpression(BaseExpression):
    logger = logging.getLogger('numeric_expression')


class UnarySign(NumericExpression):
    def __init__(self, value: BaseExpression, sign, *args, **kwargs):
        assert sign in (ss.minus_sign, ss.plus_sign)
        super().__init__(*args, **kwargs)
        self.value = value
        self.is_minus = sign == ss.minus_sign
        self.sign = -1 if self.is_minus else 1

    @property
    def convolution(self):
        self.value = self.value.convolution.to_int
        if isinstance(self.value, Int):
            return Int(self.value.value * self.sign)
        elif isinstance(self.value, Float):
            return Float(-self.value.value * self.sign)
        elif isinstance(self.value, UnarySign):
            check = self.is_minus ^ self.value.is_minus
            sign = ss.minus_sign if check else ss.plus_sign
            return UnarySign(self.value.value, sign)
        return self

    def __repr__(self):
        return '{}CastToInt({!r})'.format('-' if self.is_minus else '', self.value)


class DoubleNumericExpression(NumericExpression):
    ADD = '+'
    SUB = '-'
    MUL = '*'
    DIV = '/'
    op = None

    def __init__(self, left: BaseExpression, right: BaseExpression, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.left = left
        self.right = right

    def action(self, a, b):
        raise NotImplementedError

    def special_rules(self):
        return self

    @property
    def convolution(self):
        self.left = self.left.convolution.to_int
        self.right = self.right.convolution.to_int

        # Если два числа то производим операцию над ними
        if isinstance(self.left, PrimaryNumeric) and isinstance(self.right, PrimaryNumeric):
            value = self.action(self.left.value, self.right.value)
            if isinstance(self.left, Float) or isinstance(self.right, Float):
                return Float(value)
            return Int(value)

        # Если одно Null то все Null
        if isinstance(self.left, Null) or isinstance(self.right, Null):
            return Null()

        return self.special_rules()

    def __repr__(self):
        return '({!r} {} {!r})'.format(self.left, self.op, self.right)


class Add(DoubleNumericExpression):
    op = DoubleNumericExpression.ADD

    def action(self, a, b):
        return a + b

    def special_rules(self):
        if isinstance(self.left, PrimaryNumeric) and self.left.value == 0:
            return self.right
        if isinstance(self.right, PrimaryNumeric) and self.right.value == 0:
            return self.left
        return self


class Sub(DoubleNumericExpression):
    op = DoubleNumericExpression.SUB

    def action(self, a, b):
        return a - b

    def special_rules(self):
        if isinstance(self.left, PrimaryNumeric) and self.left.value == 0:
            return UnarySign(self.right, ss.minus_sign)
        if isinstance(self.right, PrimaryNumeric) and self.right.value == 0:
            return self.left
        return self


class Mul(DoubleNumericExpression):
    op = DoubleNumericExpression.MUL

    def action(self, a, b):
        return a * b

    def special_rules(self):
        if (
            isinstance(self.left, PrimaryNumeric) and self.left.value == 0 or
            isinstance(self.right, PrimaryNumeric) and self.right.value == 0
        ):
            return Int(0)
        return self


class Div(DoubleNumericExpression):
    op = DoubleNumericExpression.DIV

    def action(self, a, b):
        return a / b

    def special_rules(self):
        if isinstance(self.right, PrimaryNumeric) and self.right.value == 0:
            return Null()
        if isinstance(self.left, PrimaryNumeric) and self.left.value == 0:
            return Int(0)
        if isinstance(self.right, PrimaryNumeric) and self.right.value == 1:
            return self.left
        return self

    @property
    def convolution(self):
        self.left = self.left.convolution.to_int
        self.right = self.right.convolution.to_int

        # Если два числа то производим операцию над ними
        if isinstance(self.left, PrimaryNumeric) and isinstance(self.right, PrimaryNumeric):
            # Деление на 0 = Null
            if self.right.value == 0:
                return Null()
            value = self.action(self.left.value, self.right.value)
            if isinstance(self.left, Float) or isinstance(self.right, Float):
                return Float(value)
            return Int(value)

        # Если одно Null то все Null
        if isinstance(self.left, Null) or isinstance(self.right, Null):
            return Null()

        return self.special_rules()


class BooleanExpression(BaseExpression):
    logger = logging.getLogger('boolean_expression')

    def calculate(self, vector):
        raise NotImplementedError


class Not(BooleanExpression):

    def __init__(self, value: BaseExpression, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.value = value

    @property
    def convolution(self):
        self.value = self.value.convolution.to_bool
        if isinstance(self.value, ComparisonPredicate):
            self.value.op = self.value.MAP_NOT[self.value.op]
            return self.value
        elif isinstance(self.value, Bool):
            return Bool(not self.value.value)
        elif isinstance(self.value, Null):
            return Null()
        return self

    def calculate(self, vector):
        if isinstance(self.value, BooleanExpression):
            value = self.value.calculate(vector)
        else:
            value = vector.pop()
        return None if value is None else not value

    def __repr__(self):
        return 'not {!r}'.format(self.value)


class DoubleBooleanExpression(BooleanExpression):
    AND = 'and'
    OR = 'or'
    IS = 'is'
    op = None

    def __init__(self, left: BaseExpression, right: Union[BaseExpression, bool, None], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.left = left
        self.right = right

    def __repr__(self):
        return '({!r} {} {!r})'.format(self.left, self.op, self.right)

    def calculate(self, vector):
        raise NotImplementedError

    @staticmethod
    def _get_value_for_calculate(value, vector):
        if isinstance(value, BooleanExpression):
            value = value.calculate(vector)
        elif isinstance(value, Bool):
            value = value.value
        elif isinstance(value, Null):
            value = None
        else:
            value = vector.pop()
        return value


class Or(DoubleBooleanExpression):
    op = DoubleBooleanExpression.OR

    @property
    def convolution(self):
        self.left = self.left.convolution.to_bool
        self.right = self.right.convolution.to_bool

        if isinstance(self.left, Bool) and isinstance(self.right, Bool):
            return Bool(self.left.value or self.right.value)

        if (
            isinstance(self.left, Bool) and self.left.value or
            isinstance(self.right, Bool) and self.right.value
        ):
            return Bool(True)

        if (
            isinstance(self.left, Bool) and not self.left.value and
            isinstance(self.right, Bool) and not self.right.value
        ):
            return Bool(False)

        if isinstance(self.left, Null) and isinstance(self.right, Null):
            return Null()

        return self

    def calculate(self, vector):
        left = self._get_value_for_calculate(self.left, vector)
        right = self._get_value_for_calculate(self.right, vector)

        if left or right:
            return True
        elif left is None or right is None:
            return None
        return False


class And(DoubleBooleanExpression):
    op = DoubleBooleanExpression.AND

    @property
    def convolution(self):
        self.left = self.left.convolution.to_bool
        self.right = self.right.convolution.to_bool

        if isinstance(self.left, Bool) and isinstance(self.right, Bool):
            return Bool(self.left.value and self.right.value)

        if (
            isinstance(self.left, Bool) and self.left.value and
            isinstance(self.right, Bool) and self.right.value
        ):
            return Bool(True)

        if (
            isinstance(self.left, Bool) and not self.left.value or
            isinstance(self.right, Bool) and not self.right.value
        ):
            return Bool(False)

        if isinstance(self.left, Null) and isinstance(self.right, Null):
            return Null()

        return self

    def calculate(self, vector):
        left = self._get_value_for_calculate(self.left, vector)
        right = self._get_value_for_calculate(self.right, vector)

        if left is False or right is False:
            return False
        elif left and right:
            return True
        return None


class Is(DoubleBooleanExpression):
    op = DoubleBooleanExpression.IS

    @property
    def convolution(self):
        self.left = self.left.convolution.to_bool
        if isinstance(self.left, Bool):
            value = self.left.value == self.right
            return Bool(value)
        elif isinstance(self.left, Null):
            value = self.left is None
            return Bool(value)
        return self

    def calculate(self, vector):
        left = self._get_value_for_calculate(self.left, vector)
        return left is self.right


class BasePredicate(BaseExpression):
    pass


class ComparisonPredicate(BasePredicate):
    __MAP_NOT = [
        (ss.equals_operator, ss.not_equals_operator),
        (ss.less_than_operator, ss.greater_than_or_equals_operator),
        (ss.greater_than_operator, ss.less_than_or_equals_operator)
    ]
    MAP_NOT = {
        k: v
        for a, b in __MAP_NOT
        for k, v in [(a, b), (b, a)]
    }

    __MAP_REVERSE = [
        (ss.less_than_operator, ss.greater_than_operator),
        (ss.less_than_or_equals_operator, ss.greater_than_or_equals_operator)
    ]
    MAP_REVERSE = {
        k: v
        for a, b in __MAP_REVERSE
        for k, v in [(a, b), (b, a)]
    }

    def __init__(self, left, right, op, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.left = left
        self.right = right
        self.op = op

    @property
    def convolution(self):
        if isinstance(self.left, BaseExpression):
            self.left = self.left.convolution.to_int
        elif isinstance(self.right, BaseExpression):
            self.right = self.right.convolution.to_int

        if isinstance(self.left, PrimaryNumeric) and isinstance(self.right, PrimaryNumeric):
            left = self.left.value
            right = self.right.value
            if self.op == ss.equals_operator:
                return Bool(left == right)
            elif self.op == ss.not_equals_operator:
                return Bool(left != right)
            elif self.op == ss.less_than_operator:
                return Bool(left < right)
            elif self.op == ss.less_than_or_equals_operator:
                return Bool(left <= right)
            elif self.op == ss.greater_than_operator:
                return Bool(left > right)
            elif self.op == ss.greater_than_or_equals_operator:
                return Bool(left >= right)
        elif isinstance(self.left, Null) or isinstance(self.right, Null):
            return Null()
        return self

    def reverse(self):
        self.left, self.right = self.right, self.left
        self.op = self.MAP_REVERSE.get(self.op, self.op)

    def __repr__(self):
        return '({!r} {} {!r})'.format(self.left, ss.NAME_TO_SYMBOL.get(self.op), self.right)


class StringExpression(BaseExpression):
    # Todo: Does not work
    pass


class DatetimeExpression(BaseExpression):
    # Todo: Does not work
    pass
