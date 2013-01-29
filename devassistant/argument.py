class Argument(object):
    def __init__(self, *args, **kwargs):
        self.flags = args
        for k, v in kwargs.items():
            setattr(self, k, v)

    def add_argument_to(self, parser):
        parser.add_argument(*self.flags)
