class BasePredicate:
    pass


class ComparisonPredicate(BasePredicate):
    def __init__(self, left, right, op):
        self.left = left
        self.right = right
        self.op = op
