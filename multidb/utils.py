class lazy_property:
    def __init__(self, func):
        self._func = func

    def __get__(self, instance, owner):
        if instance is None:
            return None

        result = instance.__dict__[self._func.__name__] = self._func(instance)
        return result
