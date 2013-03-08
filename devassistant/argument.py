class Argument(object):
    def __init__(self, *args, **kwargs):
        self.flags = args
        self.kwargs = kwargs

    def add_argument_to(self, parser):
        """Used by cli to add this as an argument to argparse parser."""
        from devassistant.cli.devassistant_argparse import DefaultIffUsedActionFactory
        if isinstance(self.kwargs.get('action', ''), list):
            # see documentation of DefaultIffUsedActionFactory to see why this is necessary
            if self.kwargs['action'][0] == 'default_iff_used':
                self.kwargs['action'] = DefaultIffUsedActionFactory.generate_action(self.kwargs['action'][1])
        parser.add_argument(*self.flags, **self.kwargs)
