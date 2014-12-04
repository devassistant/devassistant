import getpass
import os
import re

import pytest

from devassistant import exceptions
from devassistant.argument import Argument
from devassistant.cli.devassistant_argparse import ArgumentParser

class TestArgument(object):
    p = Argument('path', '-p', '--path',
                 help='helptext',
                 nargs='?',
                 gui_hints={'type': 'path',
                            'default': '$(pwd)/foo'})

    b = Argument('bool', '-b', '--boolean',
                 action='store_true',
                 default=True)

    c = Argument('constant', '-c', '--const',
                 action='store_const',
                 const=42)

    d = Argument('posit+-ional', 'pos')

    e = Argument('+weird-ch$a#r%s', '--foo')

    f = Argument('asd', 'asd', action="store_const")  # will raise TypeError

    def test_argument_returns_correct_gui_hints(self):
        assert self.p.get_gui_hint('type') == 'path'
        assert self.p.get_gui_hint('default') == os.path.join(os.getcwd(), 'foo')

    def test_argument_returns_correct_gui_hints_if_no_hints_specified(self):
        assert self.b.get_gui_hint('type') == 'bool'
        assert self.b.get_gui_hint('default') == True

    def test_const_argument_returns_correct_gui_hints(self):
        assert self.c.get_gui_hint('type') == 'const'
        assert self.c.get_gui_hint('default') == None

    def test_argument_is_added(self, capsys):
        parser = ArgumentParser()
        self.p.add_argument_to(parser)
        parser.print_help()
        output = capsys.readouterr()[0] # captured stdout
        assert re.compile(r'-p.*--path.*helptext', re.DOTALL).search(output)

    def test_argument_to_raises_on_error(self):
        parser = ArgumentParser()
        with pytest.raises(exceptions.ExecutionException):
            self.f.add_argument_to(parser)

    def test_argument_whoami_gui_hint(self):
        a = Argument.construct_arg('some_arg',{'use':'snippet1'})
        assert a.get_gui_hint('default') == getpass.getuser()

    @pytest.mark.parametrize(('name', 'params'), [
                             ('some_arg',{'use':'snippet1'}),])
    def test_construct_arg(self, name, params):
        a = Argument.construct_arg(name, params)
        assert a.name == name
        assert a.flags == ('-s', '--some-arg')

    @pytest.mark.parametrize(('name', 'params', 'exception'), [
                             ('bar',{'use':'doesnt_exist'},exceptions.SnippetNotFoundException),
                             ('some_arg',{'use':'snippet2'},exceptions.ExecutionException),
                             ('some_arg',{'use':'snippet3'},exceptions.ExecutionException)])
    def test_construct_arg_exceptions(self, name, params, exception):
        with pytest.raises(exception):
            Argument.construct_arg(name, params)


    def test_argument_gets_default_help(self):
        assert self.c.kwargs['help'] == '(No help provided)'

    def test_proper_dest(self):
        assert self.d.get_dest() == 'posit_ional'
        assert self.e.get_dest() == 'weird_chars'
