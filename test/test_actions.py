import os
import subprocess

import pytest
from flexmock import flexmock

from devassistant import actions, exceptions
from devassistant.dapi import dapicli

from test.logger import LoggingHandler

class TestActions(object):

    def setup_class(self):
        self.ha = actions.HelpAction

    def test_get_help_contains_task_keywords(self):
        gh = self.ha().get_help()
        assert 'crt' in gh
        assert 'twk' in gh
        assert 'prep' in gh
        assert 'extra' in gh

    def test_get_help_contains_action_name(self):
        a = actions.Action()
        a.name = 'foobar_action_name'
        a.description = 'foobar_action_description'
        actions.register_action(a)

        assert 'foobar_action_name' in self.ha().get_help()
        assert 'foobar_action_description' in self.ha().get_help()

    def test_format_text_returns_original_text_on_bogus_formatting(self):
        assert self.ha().format_text('aaa', 'foo', 'bar') == 'aaa'
        assert self.ha().format_text('', 'foo', 'bar') == ''

    def test_format_text_returns_bold(self):
        assert self.ha().format_text('aaa', 'bold', 'ascii') == '\033[1maaa\033[0m'

    def test_version_action(self):
        tlh = LoggingHandler.create_fresh_handler()
        va = actions.VersionAction()
        from devassistant import __version__ as VERSION
        va.run()
        assert VERSION in tlh.msgs[0][1]


class TestDocAction(object):

    def setup_method(self, method):
        self.da = actions.DocAction
        self.tlh = LoggingHandler.create_fresh_handler()

    def test_no_docs(self):
        self.da(dap='f').run()
        assert ('INFO', 'DAP f has no documentation.') in self.tlh.msgs

    def test_lists_docs(self):
        self.da(dap='c').run()
        assert self.tlh.msgs == [
            ('INFO', 'DAP c has these docs:'),
            ('INFO', 'LICENSE'),
            ('INFO', 'doc1'),
            ('INFO', 'something/foo/doc2'),
            ('INFO', 'Use "da doc c <DOC>" to see a specific document')
        ]

    def test_displays_docs(self):
        # we only test displaying without "less" - e.g. simple logging
        flexmock(subprocess).should_receive('check_call').\
            and_raise(subprocess.CalledProcessError, None, None)
        self.da(dap='c', doc='doc1').run()
        assert ('INFO', 'Bar!\n') in self.tlh.msgs


class TestPkgSearchAction(object):

    @pytest.mark.parametrize('exc', [exceptions.DapiCommError, exceptions.DapiLocalError])
    def test_raising_exceptions(self, exc):
        flexmock(dapicli).should_receive('format_search').and_raise(exc)

        with pytest.raises(exceptions.ExecutionException):
            actions.PkgSearchAction(query='foo', noassistants=False, unstable=False,
                                    deactivated=False, minrank=0, mincount=0,
                                    allplatforms=False).run()

class TestPkgInstallAction(object):

    def setup_class(self):
        self.pkg = 'foo'
        self.exc_string = 'bar'

    @pytest.mark.parametrize(('isfile', 'method'), [
        (True, 'install_dap_from_path'),
        (False, 'install_dap')
    ])
    def test_pkg_install(self, isfile, method):
        flexmock(os.path).should_receive('isfile').with_args(self.pkg)\
                         .and_return(isfile).at_least().once()
        flexmock(dapicli).should_receive(method)\
                         .and_return([self.pkg]).at_least().once()

        # Install from path, everything goes well
        actions.PkgInstallAction(package=[self.pkg], force=False,
                                 reinstall=False, nodeps=False, __ui__='cli').run()

    def test_pkg_install_fails(self):
        flexmock(os.path).should_receive('isfile').with_args(self.pkg)\
                         .and_return(True).at_least().once()
        flexmock(dapicli).should_receive('install_dap_from_path')\
                         .and_raise(exceptions.DapiLocalError(self.exc_string)).at_least().once()

        with pytest.raises(exceptions.ExecutionException) as excinfo:
            actions.PkgInstallAction(package=[self.pkg], force=False,
                                     reinstall=False, nodeps=False, __ui__='cli').run()

        assert self.exc_string in str(excinfo.value)


class TestPkgUpdateAction(object):

    def test_pkg_update_all(self):
        '''Run update without args to update all, but everything is up to-date'''
        flexmock(dapicli).should_receive('get_installed_daps')\
                         .and_return(['foo']).at_least().once()
        flexmock(dapicli).should_receive('install_dap')\
                         .and_return([]).at_least().once()

        # Update all, everything is up to date
        actions.PkgUpdateAction(force=False, allpaths=False).run()

    def test_pkg_update_no_dapi(self):
        '''Run update of package that is not on Dapi'''
        flexmock(dapicli).should_receive('metadap')\
                         .and_return(None).at_least().once()

        with pytest.raises(exceptions.ExecutionException) as excinfo:
            actions.PkgUpdateAction(package=['foo'], force=False, allpaths=False).run()

        assert 'foo not found' in str(excinfo.value)

    def test_pkg_update_no_installed(self):
        '''Run update of package that is not installed'''
        flexmock(dapicli).should_receive('_get_metadap_dap')\
                         .and_return(({}, {'version': '0.0.1'})).at_least().once()
        flexmock(dapicli).should_receive('get_installed_version_of')\
                         .and_return(None).at_least().once()

        with pytest.raises(exceptions.ExecutionException) as excinfo:
            actions.PkgUpdateAction(package=['foo'], force=False, allpaths=False).run()

        assert 'Cannot update not yet installed DAP' in str(excinfo.value)


@pytest.mark.parametrize('action', [
    actions.PkgUninstallAction,
    actions.PkgRemoveAction
])
class TestPkgUninstallAction(object):

    def test_pkg_uninstall_dependent(self, action):
        '''Uninstall two packages, but the first depend on the latter'''
        flexmock(dapicli).should_receive('uninstall_dap')\
                         .and_return(['first', 'second']).at_least().once()

        action(package=['first', 'second'], force=True, allpaths=False, __ui__='cli').run()

    def test_pkg_uninstall_not_installed(self, action):
        '''Uninstall package that is not installed'''
        flexmock(dapicli).should_receive('get_installed_daps')\
                         .and_return(['bar']).at_least().once()

        with pytest.raises(exceptions.ExecutionException) as excinfo:
            action(package=['foo'], force=True, allpaths=False, __ui__='cli').run()

        assert 'Cannot uninstall DAP foo' in str(excinfo.value)


class TestAutoCompleteAction(object):

    def setup_class(self):
        self.aca = actions.AutoCompleteAction

        self.fake_desc = [flexmock(name=n,
                                   get_subassistants=lambda: [],
                                   args=[]) for n in ['foo', 'bar', 'baz']]
        self.fake_arg = flexmock(flags=('--qux',), kwargs=dict())
        self.fake_crt = flexmock(name='crt',
                                 get_subassistants=lambda: self.fake_desc,
                                 args=[self.fake_arg])

    @pytest.mark.parametrize('path', ['', '--debug', '__debug'])
    def test_root_path(self, path, capsys):
        expected = set(['--debug', '--help', 'create', 'doc', 'extra', 'help',
                        'pkg', 'prepare', 'tweak', 'version'])

        self.aca(path=path).run()
        stdout, _ = capsys.readouterr()

        assert stdout
        assert expected.issubset(set(stdout.split()))

    @pytest.mark.parametrize('obj', [
        flexmock(get_subassistants=lambda: []),
        flexmock(get_subactions=lambda: [])
    ])
    def test_get_descendants(self, obj):
        self.aca._get_descendants(obj)

    @pytest.mark.parametrize('obj', [
        flexmock(get_subassistants=''),
        flexmock()
    ])
    def test_get_descendants_fails(self, obj):
        with pytest.raises(TypeError):
            self.aca._get_descendants(obj)

    @pytest.mark.parametrize('path', ['crt', 'crt --qux'])
    def test_assistants(self, path, capsys):
        aca = self.aca(path=path)
        flexmock(aca).should_receive('_assistants').and_return([self.fake_crt])

        aca.run()

        stdout, _ = capsys.readouterr()

        assert not _
        assert set([a.name for a in self.fake_desc] + \
                   [f for f in self.fake_arg.flags]).issubset(set(stdout.split()))

    @pytest.mark.parametrize(('long_name', 'short_name'), [
        ('create', 'crt'),
        ('tweak', 'twk'),
        ('twk', 'mod'),
        ('prepare', 'prep'),
        ('extra', 'task'),
    ])
    def test_aliases(self, long_name, short_name, capsys):
        self.aca(path=long_name).run()
        long_stdout, _ = capsys.readouterr()

        assert long_stdout

        self.aca(path=short_name).run()
        short_stdout, _ = capsys.readouterr()

        assert short_stdout
        assert long_stdout == short_stdout

    def test_filenames(self, capsys):
        self.aca(path='pkg info').run()
        stdout, _ = capsys.readouterr()

        assert '_FILENAMES' in stdout.split()

    def test_bad_input(self, capsys):
        self.aca(path='foo bar baz').run()
        stdout, _ = capsys.readouterr()

        assert not stdout.split()
