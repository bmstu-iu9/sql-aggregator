import logging
from datetime import date, datetime
from typing import Union

from . import mixins as mx
from . import symbols as ss
from .structures import NamingChain


class BaseExpression(mx.AsMixin, mx.SignMixin, mx.NotMixin):
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
        elif isinstance(value, NamingChain):
            return Column(value)
        raise ValueError('Invalid data type: {}({})'.format(type(value), value))

    def __init__(self, value, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.value = value

    def __repr__(self):
        return '{}{}({})'.format('not ' if self.is_not else '', self.__class__.__name__, self.value)


class PrimaryNumeric(PrimaryValue):

    @property
    def convolution(self):
        if self.is_not:
            return Bool(bool(self.value))
        if self.sign == -1:
            self.value *= -1
            self.sign = 1
        return self

    @property
    def to_bool(self):
        val = bool(self.value)
        if self.is_not:
            val = not val
        return Bool(val)


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
    def convolution(self):
        assert self.sign == 1
        if self.is_not:
            self.value = not self.value
            self.is_not = False
        return self

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
            if self.is_not:
                return Bool(not bool(value))
            if isinstance(self.left, Float) or isinstance(self.right, Float):
                return Float(value)
            return Int(value)

        # Если одно Null то все Null
        if isinstance(self.left, Null) or isinstance(self.right, Null):
            return Null()

        return self.special_rules()

    def __repr__(self):
        return '{}({!r} {} {!r})'.format('not ' if self.is_not else '', self.left, self.op, self.right)


class Add(DoubleNumericExpression):
    op = DoubleNumericExpression.ADD

    def action(self, a, b):
        return a + b

    def special_rules(self):
        if isinstance(self.left, PrimaryNumeric) and self.left.value == 0:
            self.right.set_not(self.is_not)
            return self.right
        if isinstance(self.right, PrimaryNumeric) and self.right.value == 0:
            self.left.set_not(self.is_not)
            return self.left
        return self


class Sub(DoubleNumericExpression):
    op = DoubleNumericExpression.SUB

    def action(self, a, b):
        return a - b

    def special_rules(self):
        if isinstance(self.left, PrimaryNumeric) and self.left.value == 0:
            self.right.set_not(self.is_not)
            return self.right
        if isinstance(self.right, PrimaryNumeric) and self.right.value == 0:
            self.left.set_not(self.is_not)
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
            return True if self.is_not else Int(0)
        return self


class Div(DoubleNumericExpression):
    op = DoubleNumericExpression.DIV

    def action(self, a, b):
        return a / b

    def special_rules(self):
        if isinstance(self.right, PrimaryNumeric) and self.right.value == 0:
            return Null()
        if isinstance(self.left, PrimaryNumeric) and self.left.value == 0:
            return True if self.is_not else Int(0)
        if isinstance(self.right, PrimaryNumeric) and self.right.value == 1:
            self.left.set_not(self.is_not)
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
        return '{}({!r} {} {!r})'.format('not ' if self.is_not else '', self.left, self.op, self.right)


class Or(DoubleBooleanExpression):
    op = DoubleBooleanExpression.OR

    @property
    def convolution(self):
        self.left = self.left.convolution.to_bool
        self.right = self.right.convolution.to_bool

        if (
            isinstance(self.left, Bool) and self.left.value or
            isinstance(self.right, Bool) and self.right.value
        ):
            return Bool(False) if self.is_not else Bool(True)

        if (
            isinstance(self.left, Bool) and not self.left.value and
            isinstance(self.right, Bool) and not self.right.value
        ):
            return Bool(True) if self.is_not else Bool(False)

        if isinstance(self.left, Null) or isinstance(self.right, Null):
            return Null()

        return self


class And(DoubleBooleanExpression):
    op = DoubleBooleanExpression.AND

    @property
    def convolution(self):
        self.left = self.left.convolution.to_bool
        self.right = self.right.convolution.to_bool

        if (
            isinstance(self.left, Bool) and self.left.value and
            isinstance(self.right, Bool) and self.right.value
        ):
            return Bool(False) if self.is_not else Bool(True)

        if (
            isinstance(self.left, Bool) and not self.left.value or
            isinstance(self.right, Bool) and not self.right.value
        ):
            return Bool(True) if self.is_not else Bool(False)

        if isinstance(self.left, Null) or isinstance(self.right, Null):
            return Null()

        return self


class Is(DoubleBooleanExpression):
    op = DoubleBooleanExpression.IS

    @property
    def convolution(self):
        self.left = self.left.convolution.to_bool
        if isinstance(self.left, Bool):
            value = self.left.value == self.right
            return Bool(not value) if self.is_not else Bool(value)
        elif isinstance(self.left, Null):
            value = self.right is None
            return Bool(not value) if self.is_not else Bool(value)
        return self


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

    def __init__(self, left, right, op, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.left = left
        self.right = right
        self.op = op

    @property
    def convolution(self):
        self.left = self.left.convolution
        self.right = self.right.convolution
        if self.is_not:
            self.op = self.MAP_NOT[self.op]
        return self

    def __repr__(self):
        return '{}({!r} {} {!r})'.format(
            'not ' if self.is_not else '',
            self.left,
            ss.NAME_TO_SYMBOL.get(self.op),
            self.right
        )


class StringExpression(BaseExpression):
    # Todo: Does not work
    pass


class DatetimeExpression(BaseExpression):
    # Todo: Does not work
    pass
