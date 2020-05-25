class BaseJoin:
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def set_left(self, left):
        self.left = left

    def set_right(self, right):
        self.right = right

    def __repr__(self):
        return '{}({}, {})'.format(self.__class__.__name__, self.left, self.right)


class CrossJoin(BaseJoin):
    pass


class QualifiedJoin(BaseJoin):
    def __init__(self, left, right, specification):
        super().__init__(left, right)
        self.specification = specification
        self.indexed_expression = None

    def set_indexed_expression(self, expressions):
        self.indexed_expression = expressions

    def __repr__(self):
        return '{}(left={}, right={}, specification={}, indexed_expression={})'.format(
            self.__class__.__name__,
            self.left,
            self.right,
            self.specification,
            self.indexed_expression
        )


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
