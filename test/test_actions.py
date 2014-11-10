import os
import subprocess

import pytest
from flexmock import flexmock

from devassistant import actions, exceptions
from devassistant.dapi import dapicli

from test.logger import TestLoggingHandler

class TestActions(object):
    ha = actions.HelpAction

    def test_get_help_contains_task_keywords(self):
        gh = self.ha.get_help()
        assert 'crt' in gh
        assert 'twk' in gh
        assert 'prep' in gh
        assert 'extra' in gh

    def test_get_help_contains_action_name(self):
        a = actions.Action()
        a.name = 'foobar_action_name'
        a.description = 'foobar_action_description'
        actions.register_action(a)

        assert 'foobar_action_name' in self.ha.get_help()
        assert 'foobar_action_description' in self.ha.get_help()

    def test_format_text_returns_original_text_on_bogus_formatting(self):
        assert self.ha.format_text('aaa', 'foo', 'bar') == 'aaa'
        assert self.ha.format_text('', 'foo', 'bar') == ''

    def test_format_text_returns_bold(self):
        assert self.ha.format_text('aaa', 'bold', 'ascii') == '\033[1maaa\033[0m'

    def test_version_action(self, capsys):
        va = actions.VersionAction
        from devassistant import __version__ as VERSION
        va.run()
        assert VERSION in capsys.readouterr()[0]


class TestDocAction(object):
    def setup_method(self, method):
        self.da = actions.DocAction
        self.tlh = TestLoggingHandler.create_fresh_handler()

    def test_no_docs(self):
        self.da.run(dap='f')
        assert ('INFO', 'DAP "f" has no documentation.') in self.tlh.msgs

    def test_lists_docs(self):
        self.da.run(dap='c')
        assert self.tlh.msgs == [
            ('INFO', 'DAP "c" has these docs:'),
            ('INFO', 'LICENSE'),
            ('INFO', 'doc1'),
            ('INFO', 'something/foo/doc2'),
            ('INFO', 'Use "da doc c <DOC>" to see a specific document')
        ]

    def test_displays_docs(self):
        # we only test displaying without "less" - e.g. simple logging
        flexmock(subprocess).should_receive('check_call').\
            and_raise(subprocess.CalledProcessError, None, None)
        self.da.run(dap='c', doc='doc1')
        assert ('INFO', 'Bar!\n') in self.tlh.msgs


class TestPkgSearchAction(object):

    def test_raising_exceptions(self):
        flexmock(dapicli).should_receive('print_search').and_raise(Exception)

        with pytest.raises(exceptions.ExecutionException):
            actions.PkgSearchAction.run(query='foo', page='bar')

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
        actions.PkgInstallAction.run(package=[self.pkg])

    def test_pkg_install_fails(self):
        flexmock(os.path).should_receive('isfile').with_args(self.pkg)\
                         .and_return(True).at_least().once()
        flexmock(dapicli).should_receive('install_dap_from_path')\
                         .and_raise(Exception(self.exc_string)).at_least().once()

        with pytest.raises(exceptions.ExecutionException) as excinfo:
            actions.PkgInstallAction.run(package=[self.pkg])

        assert self.exc_string in str(excinfo.value)


class TestPkgUpdateAction(object):

    def test_pkg_update_all(self):
        '''Run update without args to update all, but everything is up to-date'''
        flexmock(dapicli).should_receive('get_installed_daps')\
                         .and_return(['foo']).at_least().once()
        flexmock(dapicli).should_receive('install_dap')\
                         .and_return([]).at_least().once()

        # Update all, everything is up to date
        actions.PkgUpdateAction.run()

    def test_pkg_update_no_dapi(self):
        '''Run update of package that is not on Dapi'''
        flexmock(dapicli).should_receive('metadap')\
                         .and_return(None).at_least().once()
        
        with pytest.raises(exceptions.ExecutionException) as excinfo:
            actions.PkgUpdateAction.run(package=['foo'])

        assert 'foo not found' in str(excinfo.value)

    def test_pkg_update_no_installed(self):
        '''Run update of package that is not installed'''
        flexmock(dapicli).should_receive('_get_metadap_dap')\
                         .and_return(({}, {'version': '0.0.1'})).at_least().once()
        flexmock(dapicli).should_receive('get_installed_version_of')\
                         .and_return(None).at_least().once()
        
        with pytest.raises(exceptions.ExecutionException) as excinfo:
            actions.PkgUpdateAction.run(package=['foo'])

        assert 'Cannot update not yet installed dap' in str(excinfo.value)


class TestPkgUninstallAction(object):

    def test_pkg_uninstall_dependent(self):
        '''Uninstall two packages, but the first depend on the latter'''
        flexmock(dapicli).should_receive('uninstall_dap')\
                         .and_return(['first', 'second']).at_least().once()

        actions.PkgUninstallAction.run(package=['first', 'second'], force=True)

    def test_pkg_uninstall_not_installed(self):
        '''Uninstall package that is not installed'''
        flexmock(dapicli).should_receive('get_installed_daps')\
                         .and_return(['bar']).at_least().once()

        with pytest.raises(exceptions.ExecutionException) as excinfo:
            actions.PkgUninstallAction.run(package=['foo'], force=True)

        assert 'Cannot uninstall foo' in str(excinfo.value)
