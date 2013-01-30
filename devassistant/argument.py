class Argument(object):
    def __init__(self, *args, **kwargs):
        self.flags = args
        self.kwargs = kwargs

    def add_argument_to(self, parser):
        parser.add_argument(*self.flags, **self.kwargs)
