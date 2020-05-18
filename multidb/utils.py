import logging
from functools import wraps


# noinspection PyPep8Naming
class lazy_property:
    def __init__(self, func):
        self._func = func

    def __get__(self, instance, owner):
        if instance is None:
            return None

        result = instance.__dict__[self._func.__name__] = self._func(instance)
        return result


# noinspection PyPep8Naming
class log:
    size = 0
    step = 2

    def __init__(self, logger=logging, level=logging.DEBUG, name=None):
        self.logger = logger
        self.level = level
        self.name = name

    def __call__(self, func):
        @wraps(func)
        def new_func(*args, **kwargs):
            self.logger.log(self.level, '%s> %s', ' ' * log.size, func.__name__ if self.name is None else self.name)
            log.size += log.step
            try:
                out = func(*args, **kwargs)
            finally:
                log.size -= log.step
                self.logger.log(self.level, '%s< %s', ' ' * log.size, func.__name__ if self.name is None else self.name)
            return out

        return new_func
