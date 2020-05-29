"""
Так как PyPika не имеет возможности задавать
конструкции вида `col IS TRUE` или `col IS FALSE`,
то эта возможность была добавлена при помощи этого патча.
Данный модуль необходимо импортировать
для использования данной возможности
"""
from functools import wraps
from typing import Any

import pypika


def add_method(cls):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        setattr(cls, func.__name__, wrapper)
        return func

    return decorator


class TrueCriterion(pypika.terms.NullCriterion):
    def get_sql(self, with_alias: bool = False, **kwargs: Any) -> str:
        sql = "{term} IS TRUE".format(term=self.term.get_sql(**kwargs), )
        return pypika.terms.format_alias_sql(sql, self.alias, **kwargs)


class FalseCriterion(pypika.terms.NullCriterion):
    def get_sql(self, with_alias: bool = False, **kwargs: Any) -> str:
        sql = "{term} IS FALSE".format(term=self.term.get_sql(**kwargs), )
        return pypika.terms.format_alias_sql(sql, self.alias, **kwargs)


@add_method(pypika.terms.Term)
def istrue(self) -> "TrueCriterion":
    return TrueCriterion(self)


@add_method(pypika.terms.Term)
def nottrue(self) -> "pypika.terms.Not":
    return self.istrue().negate()


@add_method(pypika.terms.Term)
def isfalse(self) -> "FalseCriterion":
    return FalseCriterion(self)


@add_method(pypika.terms.Term)
def notfalse(self) -> "pypika.terms.Not":
    return self.isfalse().negate()
