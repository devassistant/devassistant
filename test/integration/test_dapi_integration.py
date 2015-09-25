import pytest
import os

from devassistant import utils

from test import fixtures_dir
from test.integration.misc import run_da
from test.integration.misc import environ


def dap_path(fixture):
    '''Return appropriate dap path'''
    return os.path.join(fixtures_dir, 'dapi', 'daps', fixture)


class TestDAPIIntegration(object):
    @pytest.mark.webtest
    def test_installation_of_nonexistent_package(self):
        res = run_da('pkg install hope_there_is_never_dap_named_like_this', expect_error=True)
        stdout = '\n'.join(['INFO: Installing DAP hope_there_is_never_dap_named_like_this ...',
            'ERROR: DAP hope_there_is_never_dap_named_like_this not found.', ''])
        assert res.stdout == stdout

    @pytest.mark.webtest
    def test_info(self):
        # the actual output can change, so just test that this doesn't fail
        res = run_da('pkg info dap')

    @pytest.mark.webtest
    def test_list_remote(self):
        res = run_da('pkg list --simple --remote')
        assert 'common_args' in res.stdout

    def test_install_local(self):
        res = run_da('pkg install ' + dap_path('meta_only/foo-1.0.0.dap'))
        assert 'INFO: Successfully installed DAPs foo' in res.stdout

    def test_install_and_list(self):
        '''Test installed dap is listed'''
        res = run_da('pkg install ' + dap_path('meta_only/foo-1.0.0.dap'))

        res = res.run_da('pkg list --simple')
        assert res.stdout.rstrip() == 'INFO: foo'

        res = res.run_da('pkg list')
        assert 'foo' in res.stdout
        assert '1.0.0' in res.stdout

    def test_install_twice_same_path(self):
        '''Installing dap to the same path twice should fail'''
        res = run_da('pkg install ' + dap_path('meta_only/foo-1.0.0.dap'))
        res = res.run_da('pkg install ' + dap_path('meta_only/foo-1.0.0.dap'), expect_error=True)
        assert 'DAP foo is already installed' in res.stdout

    def test_install_twice_different_path(self, tmpdir):
        '''Installing already installed dap to different path should fail, unless --reinstall'''
        command = 'pkg install ' + dap_path('meta_only/foo-1.0.0.dap')
        home = tmpdir.mkdir('home')
        extra = tmpdir.mkdir('extra')

        res = run_da(command, environ=environ(home))

        env = environ(extra, home)
        res = res.run_da(command, environ=env, expect_error=True)

        assert 'DAP foo is already installed' in res.stdout

        res = res.run_da(command + ' --reinstall', environ=env)

        res = res.run_da('pkg list', environ=env)
        assert 'extra' in res.stdout
        assert 'home' in res.stdout

    def test_install_dependency_satisfied_different_path(self, tmpdir):
        '''When foo's dependencies are satisfied by a package in a different load path,
        this requirement should be deemed satisfied'''
        foo = dap_path('meta_only/foo-1.0.0.dap')
        wantsfoo = dap_path('dependencies/wantsfoo-1.0.0.dap')
        foodir = tmpdir.mkdir('foodir')
        wantsfoodir = tmpdir.mkdir('wantsfoodir')

        res = run_da('pkg install ' + foo, environ=environ(foodir))
        res = res.run_da('pkg install ' + wantsfoo, environ=environ(wantsfoodir, foodir))

    def test_install_and_uninstall(self):
        '''We should be able to uninstall installed package'''
        foo = dap_path('meta_only/foo-1.0.0.dap')
        res = run_da('pkg install ' + foo)
        res = res.run_da('pkg uninstall foo --force')  # --force as in "no confirmation needed"
        assert 'foo successfully uninstalled' in res.stdout

    def test_uninstall_not_installed(self):
        '''We should not be able to uninstall not yet installed package'''
        res = run_da('pkg uninstall foo --force', expect_error=True)
        assert 'Cannot uninstall DAP foo' in res.stdout

    def test_uninstall_no_home(self, tmpdir):
        '''By default uninstall should remove only from DEVASSISTANT_HOME'''
        foo = dap_path('meta_only/foo-1.0.0.dap')
        home = tmpdir.mkdir('home')
        extra = tmpdir.mkdir('extra')

        res = run_da('pkg install ' + foo, environ=environ(extra))
        res = res.run_da('pkg uninstall foo --force', environ=environ(home, extra),
                         expect_error=True)
        assert 'it is not in ' + str(home) in res.stdout

    def test_uninstall_allpaths(self, tmpdir):
        '''With --all-paths uninstall should remove from all paths'''
        foo = dap_path('meta_only/foo-1.0.0.dap')
        home = tmpdir.mkdir('home')
        extra = tmpdir.mkdir('extra')

        res = run_da('pkg install ' + foo, environ=environ(extra))
        res = res.run_da('pkg uninstall foo --all-paths --force', environ=environ(home, extra))

    def test_install_paths(self, tmpdir):
        '''Test where are DAPs being installed with DEVASSISTANT_NO_DEFAULT_PATH'''
        foo = dap_path('meta_only/foo-1.0.0.dap')
        home = tmpdir.mkdir('home')
        path = tmpdir.mkdir('path')
        e = environ(home, path, dont_put_home=True)

        res = run_da('pkg install ' + foo, environ=e)
        res = res.run_da('pkg list')
        assert str(path) in res.stdout
        assert not str(home) in res.stdout

    @pytest.mark.webtest
    def test_install_dapi(self):
        res = run_da('pkg install common_args')
        assert 'INFO: Successfully installed DAPs common_args' in res.stdout

    @pytest.mark.webtest
    def test_search(self):
        res = run_da('pkg search devassistant')
        assert utils.bold('devassistant') in res.stdout

    @pytest.mark.webtest
    def test_search_good_options(self):
        res = run_da('pkg search common_args --noassistants')
        assert utils.bold('common_args') in res.stdout

    @pytest.mark.webtest
    def test_search_bad_options(self):
        res = run_da('pkg search common_args', expect_error=True)
        assert 'Could not find' in res.stdout

    @pytest.mark.webtest
    def test_update_all_nothing(self):
        '''Test updating all packages when no packages are installed'''
        res = run_da('pkg update')
        assert 'No installed DAP packages found, nothing to update' in res.stdout

    @pytest.mark.webtest
    @pytest.mark.parametrize('package', ['common_args', ''])
    def test_update(self, package):
        res = run_da('pkg install ' + dap_path('meta_only/common_args-0.0.1.dap'))
        res = res.run_da('pkg update ' + package)
        assert 'DAP common_args successfully updated' in res.stdout

    @pytest.mark.webtest
    @pytest.mark.parametrize('package', ['common_args', ''])
    def test_update_different_path(self, package, tmpdir):
        '''update should install new version to DEVASSISTANT_HOME'''
        foo = dap_path('meta_only/common_args-0.0.1.dap')
        foodir = tmpdir.mkdir('foodir')
        home = tmpdir.mkdir('home')

        # install old common_args to foodir
        res = run_da('pkg install ' + foo, environ=environ(foodir))

        # update with different home
        res = res.run_da('pkg update ' + package, environ=environ(home, foodir))

        # update goes fine
        assert 'DAP common_args successfully updated' in res.stdout

        # check we have both versions
        res = res.run_da('pkg list', environ=environ(foodir))
        assert '0.0.1' in res.stdout

        res = res.run_da('pkg list', environ=environ(home))
        assert 'common_args' in res.stdout
        assert '0.0.1' not in res.stdout

    @pytest.mark.webtest
    @pytest.mark.parametrize('package', ['common_args', ''])
    def test_update_all_paths(self, package, tmpdir):
        '''update with --all-paths in all paths'''
        foo = dap_path('meta_only/common_args-0.0.1.dap')
        foodir = tmpdir.mkdir('foodir')
        home = tmpdir.mkdir('home')

        # install old common_args to foodir
        res = run_da('pkg install ' + foo, environ=environ(foodir))

        # update with different home
        res = res.run_da('pkg update --all-paths ' + package, environ=environ(home, foodir))

        # update goes fine
        assert 'DAP common_args successfully updated' in res.stdout

        # check we have new version in foodir
        # and no version in home
        res = res.run_da('pkg list', environ=environ(home, foodir))
        assert 'common_args' in res.stdout
        assert '0.0.1' not in res.stdout
        assert str(foodir) in res.stdout
        assert str(home) not in res.stdout
