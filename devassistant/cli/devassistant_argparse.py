import argparse

from gettext import gettext as _

from devassistant import settings
from devassistant.actions import HelpAction


class ArgumentParser(argparse.ArgumentParser):
    def __init__(self, *args, **kwargs):
        super(ArgumentParser, self).__init__(*args, **kwargs)

    def error(self, message):
        import sys as _sys
        # dirty hack - only top level binary has suppressed usage
        if self.usage == argparse.SUPPRESS:
            wants_help = '-h' in _sys.argv or '--help' in _sys.argv
            if not wants_help:
                print('Couldn\'t parse input, displaying help ...\n')
            print(HelpAction.get_help())
            if wants_help:
                self.exit(0)
            else:
                self.exit(1)
        else:
            # python 2 and 3 hooks to grab missing subassistant argument and report it meaningfully
            if message == _('too few arguments') or settings.SUBASSISTANT_N_STRING[:-3] in message:
                for action in self._get_positional_actions():
                    if isinstance(action, argparse._SubParsersAction):
                        if message == _('too few arguments') and len(action.choices) == 0:
                            self.exit(2, _('No subassistants available.\n'))
                        else:
                            self.print_usage(_sys.stderr)
                            self.exit(2, _('You have to select a subassistant.\n'))
            self.print_usage(_sys.stderr)
            self.exit(1, _('%s: error: %s\n') % (self.prog, message))


class DefaultIffUsedActionFactory(object):
    """Argparse doesn't cover one usecase of default values:
    Let's have an argument -e and it's default value 'foo'. You need:

    $ myprog # no arguments => no 'e' in Namespace
    $ myprog -e # -e without argument => use default 'foo' for 'e'
    $ myprog -e bar # -e with argument => use value 'bar' for 'e'

    This is undoable in argparse. So this class generates an Action class
    that does this. Usage:

    >>> parser.add_argument('-e', action=DefaultIffUsedActionFactory.generate_action(['foo']))

    Note that this will not work if you pass default to add_argument!
    """
    @classmethod
    def generate_action(cls, default):
        class DefaultIffUsedAction(argparse.Action):
            def __call__(self, parser, namespace, values, option_string):
                if values:
                    setattr(namespace, self.dest, values)
                else:
                    setattr(namespace, self.dest, default)

        return DefaultIffUsedAction
