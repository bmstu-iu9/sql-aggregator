import logging

from . import symbols as ss


class SignMixin:
    logger = logging.getLogger('sign_mixin')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sign = 1

    def set_sign(self, sign):
        if sign == ss.minus_sign:
            self.sign *= -1


class NotMixin:
    logger = logging.getLogger('not_mixin')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_not = False

    def set_not(self, flag=True):
        if flag:
            self.is_not = not self.is_not


class AsMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.short_name = None

    def as_(self, name):
        self.short_name = name
