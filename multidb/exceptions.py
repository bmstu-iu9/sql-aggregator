class ParseException(Exception):
    pass


class ParseDateException(ParseException):
    pass


class ParseDatetimeException(ParseException):
    pass


class NotSupported(Exception):
    pass
