import os
import re

from devassistant.argument import Argument
from devassistant.cli.devassistant_argparse import ArgumentParser

class TestArgument(object):
    p = Argument('-p', '--path',
                 help='helptext',
                 nargs='?',
                 gui_hints={'type': 'path',
                            'default': '$(pwd)/foo'})
    b = Argument('-b', '--boolean',
                 action='store_true',
                 default=True)

    def test_argument_returns_correct_gui_hints(self):
        assert self.p.get_gui_hint('type') == 'path'
        assert self.p.get_gui_hint('default') == os.path.join(os.getcwd(), 'foo')

    def test_argument_returns_correct_gui_hints_if_no_hints_specified(self):
        assert self.b.get_gui_hint('type') == 'bool'
        assert self.b.get_gui_hint('default') == True

    def test_argument_is_added(self, capsys):
        parser = ArgumentParser()
        self.p.add_argument_to(parser)
        parser.print_help()
        output = capsys.readouterr()[0] # captured stdout
        assert re.compile('-p.*helptext').search(output)
