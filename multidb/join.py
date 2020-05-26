from itertools import product, groupby
from . import utils


def brute_force(left, right, num, specification):
    for lrow, rrow in product(left, right):
        new_row = lrow + rrow
        if specification.express(new_row, num):
            yield new_row


class BaseJoin:
    def __init__(self, left, right):
        self.left = left
        self.right = right
        self.sorted_columns = []

    @utils.lazy_property
    def size(self):
        return self.left.size + self.right.size

    def set_left(self, left):
        self.left = left

    def set_right(self, right):
        self.right = right

    def action(self, left, right, num):
        raise NotImplementedError()

    def get_cursor(self, num):
        raise NotImplementedError()

    def __repr__(self):
        return '{}({}, {})'.format(self.__class__.__name__, self.left, self.right)


class CrossJoin(BaseJoin):
    def action(self, left, right, num):
        for lrow, rrow in product(left, right):
            yield lrow + rrow

    def get_cursor(self, num):
        left_num, left = self.left.get_cursor(num + 1)
        right_num, right = self.right.get_cursor(left_num + 1)

        cursor = self.action(left, right, num)
        self.sorted_columns = self.left.sorted_columns
        return right_num, cursor


class QualifiedJoin(BaseJoin):
    def __init__(self, left, right, specification):
        super().__init__(left, right)
        self.specification = specification
        self.indexed_expression = None

    def set_indexed_expression(self, expressions):
        self.indexed_expression = expressions

    def action(self, left, right, num):
        raise NotImplementedError()

    def get_cursor(self, num):
        left_num, left = self.left.get_cursor(num + 1)
        right_num, right = self.right.get_cursor(left_num + 1)

        if not self.indexed_expression:
            self.sorted_columns = self.left.sorted_columns
            cursor = brute_force(left, right, num, self.specification)
        else:
            if (
                    len(self.indexed_expression) > self.left.sorted_columns or
                    any(
                        lft not in scols
                        for (lft, rght), scols in zip(self.indexed_expression, self.left.sorted_columns)
                    )
            ):
                lsc = [(a,) for a, b in self.indexed_expression]
                lipos = [a.idx(num) for a, in lsc]
                left = sorted(left, key=lambda x: tuple(x[i] for i in lipos))
            else:
                lsc = self.left.sorted_columns

            if (
                    len(self.indexed_expression) > self.right.sorted_columns or
                    any(
                        rght not in scols
                        for (lft, rght), scols in zip(self.indexed_expression, self.left.sorted_columns)
                    )
            ):
                rsc = [(b,) for a, b in self.indexed_expression]
                ripos = [b.idx(num) for b, in rsc]
                right = sorted(left, key=lambda x: tuple(x[i] for i in ripos))
            else:
                rsc = self.right.sorted_columns

            self.sorted_columns = [
                left + right
                for left, right in zip(lsc, rsc)
            ]
            cursor = self.action(left, right, num)
        return right_num, cursor

    def __repr__(self):
        return '{}(left={}, right={}, specification={}, indexed_expression={})'.format(
            self.__class__.__name__,
            self.left,
            self.right,
            self.specification,
            self.indexed_expression
        )


class InnerJoin(QualifiedJoin):
    def action(self, left, right, num):
        """
        Копипаста много, но возможно будет быстрее работать
        """
        lipos, ripos = zip(*[(a.idx(num), b.idx(num)) for a, b in self.indexed_expression])

        group_left = groupby(left, key=lambda x: tuple(x[i] for i in lipos))
        group_right = groupby(right, key=lambda x: tuple(x[i] for i in ripos))

        try:
            lidx, lrows = next(group_left)
        except StopIteration:
            return

        try:
            ridx, rrows = next(group_right)
        except StopIteration:
            return

        while True:

            if any(x is None for x in lidx):
                try:
                    lidx, lrows = next(left)
                except StopIteration:
                    return
            elif any(x is None for x in ridx):
                try:
                    ridx, rrows = next(ridx)
                except StopIteration:
                    return
            elif lidx == ridx:
                for lrow, rrow in product(lrows, rrows):
                    row = lrow + rrow
                    if self.specification.calculate(row):
                        yield row
                try:
                    lidx, lrows = next(left)
                    ridx, rrows = next(ridx)
                except StopIteration:
                    return

            elif lidx > ridx:
                try:
                    ridx, rrows = next(ridx)
                except StopIteration:
                    return

            else:  # lidx < ridx
                try:
                    lidx, lrows = next(left)
                except StopIteration:
                    return


class OuterJoin(QualifiedJoin):
    def action(self, left, right, num):
        raise NotImplementedError()


class LeftJoin(OuterJoin):
    def action(self, left, right, num):
        """
        Копипаста много, но возможно будет быстрее работать
        """
        lipos, ripos = zip(*[(a.idx(num), b.idx(num)) for a, b in self.indexed_expression])

        group_left = groupby(left, key=lambda x: tuple(x[i] for i in lipos))
        group_right = groupby(right, key=lambda x: tuple(x[i] for i in ripos))

        try:
            lidx, lrows = next(group_left)
        except StopIteration:
            return

        try:
            ridx, rrows = next(group_right)
        except StopIteration:
            for row in lrows:
                yield row + (None,) * self.right.size
            for _, rows in group_left:
                for row in rows:
                    yield row + (None,) * self.right.size
            return

        while True:

            if any(x is None for x in lidx):
                try:
                    for row in lrows:
                        yield row + (None,) * self.right.size
                    lidx, lrows = next(left)
                except StopIteration:
                    return
            elif any(x is None for x in ridx):
                try:
                    ridx, rrows = next(ridx)
                except StopIteration:
                    for row in lrows:
                        yield row + (None,) * self.right.size
                    for _, rows in group_left:
                        for row in rows:
                            yield row + (None,) * self.right.size
                    return
            elif lidx == ridx:
                for lrow, rrow in product(lrows, rrows):
                    row = lrow + rrow
                    if self.specification.calculate(row):
                        yield row

                try:
                    lidx, lrows = next(left)
                except StopIteration:
                    return

                try:
                    ridx, rrows = next(group_right)
                except StopIteration:
                    for row in lrows:
                        yield row + (None,) * self.right.size
                    for _, rows in group_left:
                        for row in rows:
                            yield row + (None,) * self.right.size
                    return

            elif lidx > ridx:
                try:
                    ridx, rrows = next(ridx)
                except StopIteration:
                    return

            else:  # lidx < ridx
                try:
                    for row in lrows:
                        yield row + (None,) * self.right.size
                    lidx, lrows = next(left)
                except StopIteration:
                    return


class RightJoin(OuterJoin):
    pass


class FullJoin(OuterJoin):
    pass


DEFAULT_JOIN = LeftJoin
