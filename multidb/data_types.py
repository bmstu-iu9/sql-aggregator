from typing import Union

from . import expression as expr
from . import utils

NonparenthesizedValueExpressionPrimary = expr.PrimaryValue

Literal = expr.PrimaryValue
UnsignedLiteral = expr.PrimaryValue
GeneralLiteral = expr.PrimaryValue
SignedNumericLiteral = expr.PrimaryValue
UnsignedNumericLiteral = expr.PrimaryValue

IdentifierChain = utils.NamingChain
TruthValue = Union[bool, None]

NumericValueExpression = Union[expr.NumericExpression, expr.SimpleExpression]
BooleanValueExpression = Union[expr.BooleanExpression, expr.SimpleExpression]
ValueExpression = Union[NumericValueExpression, BooleanValueExpression]


ComparisonPredicate = expr.ComparisonPredicate
BooleanPrimary = Union[ComparisonPredicate,
                       ValueExpression,
                       NonparenthesizedValueExpressionPrimary]
BooleanTest = Union[BooleanPrimary, expr.Is]

RowValueSpecialCase = Union[ValueExpression, Literal]
ValueExpressionPrimary = Union[ValueExpression, NonparenthesizedValueExpressionPrimary]
