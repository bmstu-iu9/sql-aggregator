class ParseException(Exception):
    pass


class ParseDateException(ParseException):
    pass


class ParseDatetimeException(ParseException):
    pass


class NotSupported(Exception):
    pass


class SyntaxException(Exception):
    pass


class FatalSyntaxException(SyntaxException):
    pass
