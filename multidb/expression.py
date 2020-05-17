import logging

from . import symbols as ss


class BaseExpression:
    def __init__(self):
        self.name = None

    def as_(self, name):
        self.name = name


class NumericExpression(BaseExpression):
    logger = logging.getLogger('numeric_expression')
    pass


class PrimaryNumericExpression(NumericExpression):
    def __init__(self, expr):
        super().__init__()
        self.expr = expr
        self.sign = 1

    def set_sign(self, sign):
        if sign == ss.plus_sign:
            self.sign = 1
        elif sign == ss.minus_sign:
            self.sign = -1
        else:
            self.logger.error('Wrong sign <%s>', sign)


class DoubleNumericExpression(NumericExpression):
    def __init__(self, left, right):
        super().__init__()
        self.left = left
        self.right = right


class AddNumericExpression(DoubleNumericExpression):
    pass


class SubNumericExpression(DoubleNumericExpression):
    pass


class MulNumericExpression(DoubleNumericExpression):
    pass


class DivNumericExpression(DoubleNumericExpression):
    pass


class StringExpression(BaseExpression):
    pass


class DatetimeExpression(BaseExpression):
    pass


class BooleanExpression(BaseExpression):
    logger = logging.getLogger('boolean_expression')


class PrimaryBooleanExpression(BooleanExpression):
    def __init__(self, expr):
        super().__init__()
        self.expr = expr
        self.is_not = False

    def set_not(self, not_):
        self.is_not = not_


class DoubleBooleanExpression(BooleanExpression):
    def __init__(self, left, right):
        super().__init__()
        self.left = left
        self.right = right


class OrBooleanExpression(DoubleBooleanExpression):
    pass


class AndBooleanExpression(DoubleBooleanExpression):
    pass


class IsBooleanExpression(DoubleBooleanExpression):
    def __init__(self, left, right, is_not):
        super().__init__(left, right)
        self.is_not = is_not
