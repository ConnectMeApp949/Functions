class lg_logger:
    def __init__(self, level):
        self.level = level
    def f(self, *args):
        if self.level > -1:
            for m in args:
                print(m)
    def e(self, *args):
        if self.level > 0:
            for m in args:
                print(m)
    def w(self, *args):
        if self.level > 1:
            for m in args:
                print(m)
    def i(self, *args):
        if self.level > 2:
            for m in args:
                print(m)
    def d(self, *args):
        if self.level > 3:
            for m in args:
                print(m)
    def t(self, *args):
        if self.level > 4:
            for m in args:
                print(m)