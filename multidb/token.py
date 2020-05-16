import ast
import re
from datetime import datetime

from .exceptions import ParseDateException, ParseDatetimeException


class BaseToken:
    INT = 0
    FLOAT = 1
    STRING = 2
    DATE = 3
    DATETIME = 4
    IDENTIFIER = 5
    KEYWORD = 6

    kind = None
    regexp = None

    @classmethod
    def match(cls, pos):
        match = cls.regexp.match(pos.text)
        return (match.end(), match) if match else (0, None)

    def __init__(self, start, end, match):
        self.start = start.copy()
        self.end = end.copy()
        self.match = match

    def raw_value(self, match=None):
        return match.group() if match else self.match.group()

    def decode(self):
        raise NotImplementedError(
            'Необходимо определить метод decode в {}'.format(self.__class__.__name__)
        )


class IntToken(BaseToken):
    kind = BaseToken.INT
    regexp = re.compile(r'[1-9]\d*|0')

    def decode(self):
        return int(super().decode())


class FloatToken(BaseToken):
    kind = BaseToken.FLOAT
    regexp = re.compile(r'([1-9]\d*|0)?\.\d+|([1-9]\d*|0)\.')

    def decode(self):
        return float(self.raw_value())


class StringToken(BaseToken):
    kind = BaseToken.STRING
    regexp = re.compile(r'\'([^\\\']|\\.)*\'')

    def decode(self):
        return ast.literal_eval(self.raw_value())


class DateToken(StringToken):
    kind = BaseToken.DATE
    regexp = re.compile(r'\'\d{4}-\d{2}-\d{2}\'')

    def decode(self):
        str_date = super().decode()
        try:
            return datetime.strptime(str_date, '%Y-%m-%d').date()
        except ValueError as ex:
            raise ParseDateException(str(ex))


class DatetimeToken(StringToken):
    kind = BaseToken.DATETIME
    regexp = re.compile(r'\'\d{4}-\d{2}-\d{2} \d{2}-\d{2}-\d{2}\'')

    def decode(self):
        str_date = super().decode()
        try:
            return datetime.strptime(str_date, '%Y-%m-%d %H:%M:%S').date()
        except ValueError as ex:
            raise ParseDatetimeException(str(ex))


class IdentifierToken(BaseToken):
    kind = BaseToken.IDENTIFIER
    regexp = re.compile(r'[a-zA-Z_][a-zA-Z_0-9]*')

    def decode(self):
        return self.raw_value()


class KeywordToken(IdentifierToken):
    kind = BaseToken.KEYWORD
    KEYWORDS = {}

    @classmethod
    def match(cls, pos):
        size, match = super().match()
        if match and match.group().upper() in cls.KEYWORDS:
            return size, match
        return 0, None
