import ast
import re
from datetime import datetime

from . import keywords as kw
from . import symbols as ss
from . import utils
from .exceptions import ParseDateException, ParseDatetimeException


class BaseToken:
    INT = 0
    FLOAT = 1
    STRING = 2
    DATE = 3
    DATETIME = 4
    IDENTIFIER = 5
    KEYWORD = 6
    SYMBOL = 7

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

    @utils.lazy_property
    def raw_value(self):
        return self.match.group()

    @utils.lazy_property
    def decode(self):
        raise NotImplementedError(
            'Необходимо определить метод decode в {}'.format(self.__class__.__name__)
        )


class IntToken(BaseToken):
    kind = BaseToken.INT
    regexp = re.compile(r'[1-9]\d*|0')

    @utils.lazy_property
    def decode(self):
        return int(super().raw_value)


class FloatToken(BaseToken):
    kind = BaseToken.FLOAT
    regexp = re.compile(r'([1-9]\d*|0)?\.\d+|([1-9]\d*|0)\.')

    @utils.lazy_property
    def decode(self):
        return float(self.raw_value)


class StringToken(BaseToken):
    kind = BaseToken.STRING
    regexp = re.compile(r'\'([^\\\']|\\.)*\'')

    @utils.lazy_property
    def decode(self):
        return ast.literal_eval(self.raw_value())


class DateToken(StringToken):
    kind = BaseToken.DATE
    regexp = re.compile(r'\'\d{4}-\d{2}-\d{2}\'')

    @utils.lazy_property
    def decode(self):
        str_date = super().decode
        try:
            return datetime.strptime(str_date, '%Y-%m-%d').date()
        except ValueError as ex:
            raise ParseDateException(str(ex))


class DatetimeToken(StringToken):
    kind = BaseToken.DATETIME
    regexp = re.compile(r'\'\d{4}-\d{2}-\d{2} \d{2}-\d{2}-\d{2}\'')

    @utils.lazy_property
    def decode(self):
        str_date = super().decode
        try:
            return datetime.strptime(str_date, '%Y-%m-%d %H:%M:%S').date()
        except ValueError as ex:
            raise ParseDatetimeException(str(ex))


class IdentifierToken(BaseToken):
    kind = BaseToken.IDENTIFIER
    regexp = re.compile(r'[a-zA-Z_][a-zA-Z_0-9]*')

    @utils.lazy_property
    def decode(self):
        return self.raw_value


class KeywordToken(IdentifierToken):
    kind = BaseToken.KEYWORD

    RESERVED_WORDS = kw.RESERVED_WORDS
    NON_RESERVED_WORDS = kw.NON_RESERVED_WORDS

    @classmethod
    def match(cls, pos):
        size, match = super().match()
        if match:
            val = match.group().upper()
            if val in cls.RESERVED_WORDS or val in cls.NON_RESERVED_WORDS:
                return size, match
        return 0, None

    def __init__(self, start, end, match):
        super().__init__(start, end, match)
        self.is_reserved = self.decode in self.RESERVED_WORDS

    @utils.lazy_property
    def decode(self):
        return super().decode.upper()


class SymbolToken(BaseToken):
    kind = BaseToken.SYMBOL
    NAME_TO_SYMBOL = ss.NAME_TO_SYMBOL
    SYMBOL_TO_NAME = ss.SYMBOL_TO_NAME
    regexp = re.compile(r'|'.join(re.escape(s) for n, s in ss.SPEC_SYMBOLS))

    @utils.lazy_property
    def decode(self):
        return self.SYMBOL_TO_NAME[self.raw_value]
