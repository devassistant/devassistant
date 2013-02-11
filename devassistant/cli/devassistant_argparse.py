import argparse

from gettext import gettext as _

from devassistant import exceptions
from devassistant import settings

class ArgumentParser(argparse.ArgumentParser):
    def __init__(self, *args, **kwargs):
        super(ArgumentParser, self).__init__(*args, **kwargs)

    def error(self, message):
        import sys as _sys
        self.print_usage(_sys.stderr)
        # python 2 and 3 hooks to grab missing subassistant argument and report it meaningfully
        if message == _('too few arguments') or settings.SUBASSISTANT_N_STRING[:-3] in message:
            for action in self._get_positional_actions():
                if isinstance(action, argparse._SubParsersAction):
                    self.exit(2, _('You have to select a subassistant.\n'))
        self.exit(1, _('%s: error: %s\n') % (self.prog, message))
