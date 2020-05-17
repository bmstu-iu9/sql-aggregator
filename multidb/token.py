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
    END = 8

    kind = None
    regexp = None

    @classmethod
    def match(cls, pos):
        match = cls.regexp.match(pos.text)
        return (match.end(), match) if match else (0, None)

    def __init__(self, match, interval):
        self.match = match
        self.interval = interval

    @utils.lazy_property
    def raw_value(self):
        return self.match.group()

    @utils.lazy_property
    def decode(self):
        raise NotImplementedError(
            'Необходимо определить метод decode в {}'.format(self.__class__.__name__)
        )

    def check_type(self, other):
        return isinstance(other, type) and self.__class__ == other

    def __str__(self):
        return '{}({})'.format(self.__class__.__name__, self.decode)

    def __repr__(self):
        return '{}({!r}->{})'.format(self.__class__.__name__, self.raw_value, self.decode)


class IntToken(BaseToken):
    kind = BaseToken.INT
    regexp = re.compile(r'(?:[1-9]\d*|0)(?![0-9A-Za-z_])')

    @utils.lazy_property
    def decode(self):
        return int(super().raw_value)


class FloatToken(BaseToken):
    kind = BaseToken.FLOAT
    regexp = re.compile(r'(?:([1-9]\d*|0)?\.\d+|([1-9]\d*|0)\.)(?![0-9A-Za-z_])')

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
    regexp = re.compile(r'[a-zA-Z_][a-zA-Z_0-9]*|`[a-zA-Z_][a-zA-Z_0-9]*`')

    @utils.lazy_property
    def decode(self):
        return self.raw_value.strip('`')


class KeywordToken(IdentifierToken):
    kind = BaseToken.KEYWORD

    RESERVED_WORDS = kw.RESERVED_WORDS
    NON_RESERVED_WORDS = kw.NON_RESERVED_WORDS

    @classmethod
    def match(cls, pos):
        size, match = super().match(pos)
        if match:
            val = match.group().upper()
            if val in cls.RESERVED_WORDS or val in cls.NON_RESERVED_WORDS:
                return size, match
        return 0, None

    def __init__(self, match, interval):
        super().__init__(match, interval)
        self.is_reserved = self.decode in self.RESERVED_WORDS

    @utils.lazy_property
    def decode(self):
        return super().decode.upper()

    def check_type(self, other):
        return isinstance(other, str) and self.decode == other


class SymbolToken(BaseToken):
    kind = BaseToken.SYMBOL
    NAME_TO_SYMBOL = ss.NAME_TO_SYMBOL
    SYMBOL_TO_NAME = ss.SYMBOL_TO_NAME
    regexp = re.compile(r'|'.join(re.escape(s) for n, s in ss.SPEC_SYMBOLS))

    @utils.lazy_property
    def decode(self):
        return self.SYMBOL_TO_NAME[self.raw_value]

    def check_type(self, other):
        return isinstance(other, str) and self.decode == other


class EndToken(BaseToken):
    kind = BaseToken.END

    def __init__(self, match=None, interval=None):
        super().__init__(match, interval)

    @utils.lazy_property
    def raw_value(self):
        return None

    @utils.lazy_property
    def decode(self):
        return None

    def __str__(self):
        return self.__class__.__name__
