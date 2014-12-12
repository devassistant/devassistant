import argparse
import sys

from gettext import gettext as _

from devassistant import bin
from devassistant import settings
from devassistant.actions import HelpAction

class ArgumentParser(argparse.ArgumentParser):
    no_assistants_msg = '\n'.join([
        'No subassistants available.',
        '',
        'To search DevAssistant Package Index (DAPI) for new assistants,',
        'you can either browse https://dapi.devassistant.org/ or run',
        '',
        '"da pkg search <term>".',
        '',
        'Then you can run',
        '',
        '"da pkg install <DAP-name>"',
        '',
        'to install the desired DevAssistant package (DAP).\n'])

    def __init__(self, *args, **kwargs):
        super(ArgumentParser, self).__init__(*args, **kwargs)

    def error(self, message):
        # dirty hack - only top level binary has suppressed usage
        if self.usage == argparse.SUPPRESS:
            wants_help = '-h' in sys.argv or '--help' in sys.argv
            if not wants_help:
                print('Couldn\'t parse input, displaying help ...\n')
            print(HelpAction.get_help())
            if wants_help:
                self.exit(0)
            else:
                self.exit(1)
        else:
            if message == _('too few arguments') or settings.SUBASSISTANT_N_STRING[:-3] in message:
                self._bad_subassistant_error(message)
            self.print_usage(sys.stderr)
            self.exit(1, _('%s: error: %s\n') % (self.prog, message))

    def _bad_subassistant_error(self, message):
        # python 2 and 3 hooks to grab wrong/missing subassistant and report it meaningfully
        for action in self._get_positional_actions():
            if isinstance(action, argparse._SubParsersAction):
                if len(action.choices) == 0:
                    self.exit(2, _(self.no_assistants_msg))
                else:
                    self.print_usage(sys.stderr)
                    prog = getattr(action, '_prog_prefix', 'crt').split()[0]
                    all_assistants_names = []
                    for a in bin.TopAssistant().get_subassistants():
                        all_assistants_names.extend(a.get_all_names())
                    if prog in all_assistants_names:
                        not_found = 'Assistant'
                        select = 'subassistant'
                    else:
                        not_found = 'Action'
                        select = 'subaction'

                    if 'invalid choice' in message:
                        a = self._format_wrong_subparser_path(action)
                        self.exit(2, _('{0} not found: "{1}"\n'.format(not_found, a)))
                    else:
                        self.exit(2, _('You have to select a {0}.\n'.format(select)))

    def _format_wrong_subparser_path(self, action):
        argv = sys.argv
        subparser_start = getattr(action, '_prog_prefix', '').split()
        if subparser_start == []:
            return '<internal error - no _prog_prefix>'

        # We have to match members of argv with members of subparser start;
        #  The hard part is that if argv is ['crt', '--deps-only', '--blah', 'assistant'],
        #  then subparser_start is ['crt', 'assistant'].
        #  In fact we're searching for first member of argv not prefixed with "-"
        #  which is not in subparser_start.
        subparser_start_pos = 0
        wrong_subparser = None
        for s in argv:
            # skip all argv members before we find the one at subparser_start_pos
            if subparser_start_pos < len(subparser_start):
                if s == subparser_start[subparser_start_pos]:
                    subparser_start_pos += 1
            else:
                # we've reached end of subparser_start, get first memeber not prefixed with "-"
                if not s.startswith('-'):
                    wrong_subparser = s
                    break
        if not wrong_subparser:
            return '<internal error - wrong_subparser not found>'
        return ' '.join(subparser_start + [wrong_subparser])


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
