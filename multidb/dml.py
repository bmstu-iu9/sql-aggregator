class Selection:
    def __init__(self, select_list, from_, where=None, group=None, having=None):
        self.select_list = select_list
        self.from_ = from_
        self.where = where
        self.group = group
        self.having = having
