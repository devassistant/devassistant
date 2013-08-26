import os

class Argument(object):
    """Represents assistant argument, that can either be added to argparse parser
    or interpreted otherwise by any frontend."""

    def __init__(self, name, *args, **kwargs):
        self.name = name
        self.flags = args
        self.gui_hints = kwargs.pop('gui_hints', {})
        self.kwargs = kwargs

    def add_argument_to(self, parser):
        """Used by cli to add this as an argument to argparse parser.

        Args:
            parser: parser to add this argument to
        """
        from devassistant.cli.devassistant_argparse import DefaultIffUsedActionFactory
        if isinstance(self.kwargs.get('action', ''), list):
            # see documentation of DefaultIffUsedActionFactory to see why this is necessary
            if self.kwargs['action'][0] == 'default_iff_used':
                self.kwargs['action'] = DefaultIffUsedActionFactory.generate_action(
                                                                        self.kwargs['action'][1])
        parser.add_argument(*self.flags, **self.kwargs)

    def get_gui_hint(self, hint):
        """Returns the value for specified gui hint (or a sensible default value,
        if this argument doesn't specify the hint).

        Args:
            hint: name of the hint to get value for
        Returns:
            value of the hint specified in yaml or a sensible default
        """
        if hint == 'type':
            if self.kwargs.get('action') == 'store_true':
                return 'bool'
            return self.gui_hints.get('type', 'str')
        elif hint == 'default':
            hint_type = self.get_gui_hint('type')
            hint_default = self.gui_hints.get('default', None)
            arg_default = self.kwargs.get('default', None)

            if hint_type == 'path':
                if hint_default != None:
                    default = hint_default.replace('$(pwd)', os.getcwd())
                else:
                    default = arg_default or '~'
                return os.path.abspath(os.path.expanduser(default))
            elif hint_type == 'bool':
                return hint_default or arg_default or False
            else:
                return hint_default or arg_default or ''
