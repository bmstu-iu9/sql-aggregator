class BaseJoin:
    def __init__(self, right):
        self.left = None
        self.right = right

    def set_left(self, left):
        self.left = left

    def __repr__(self):
        return '{}({}, {})'.format(self.__class__.__name__, self.left, self.right)


class CrossJoin(BaseJoin):
    pass


class QualifiedJoin(BaseJoin):
    def __init__(self, right, specification):
        super().__init__(right)
        self.specification = specification

    def __repr__(self):
        return '{}({}, {}, {})'.format(self.__class__.__name__, self.left, self.right, self.specification)


class InnerJoin(QualifiedJoin):
    pass


class OuterJoin(QualifiedJoin):
    pass


class LeftJoin(OuterJoin):
    pass


class RightJoin(OuterJoin):
    pass


class FullJoin(OuterJoin):
    pass


DEFAULT_JOIN = LeftJoin
