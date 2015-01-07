import os
import pytest
import six

from flexmock import flexmock

from devassistant import package_managers, utils, settings
from devassistant.exceptions import ClException, DependencyException,\
                                    NoPackageManagerOperationalException,\
                                    NoPackageManagerException
from devassistant.command_helpers import ClHelper, DialogHelper

def module_not_available(module):
    try:
        six.moves.builtins.__import__(module)
        return False
    except ImportError:
        return True

class TestRPMPackageManager(object):

    def setup_method(self, method):
        self.rpm = package_managers.RPMPackageManager

    @pytest.mark.parametrize('result', [True, False])
    def test_is_rpm_installed(self, result):
        flexmock(ClHelper).should_receive('run_command')\
                .with_args('rpm -q --whatprovides "foo"').and_return(result)
        assert self.rpm.is_rpm_installed('foo') is result

    def test_was_rpm_installed(self):
        pass


class TestYUMPackageManager(object):

    def setup_method(self, method):
        self.ypm = package_managers.YUMPackageManager

    @pytest.mark.parametrize(('group', 'output', 'result'), [
        ('foo', 'Installed Groups', 'foo'),
        ('bar', '', False)
    ])
    def test_is_group_installed(self, group, output, result):
        flexmock(ClHelper).should_receive('run_command')\
                .with_args('yum group list "{grp}"'.format(grp=group)).and_return(output)
        assert self.ypm.is_group_installed(group) == result

    def test_install(self):
        pkgs = ('foo', 'bar', 'baz')

        flexmock(ClHelper).should_receive('run_command')
        assert self.ypm.install(*pkgs) == pkgs

        flexmock(ClHelper).should_receive('run_command').and_raise(ClException(None, None, None))
        assert self.ypm.install(*pkgs) is False

    def test_works(self):
        mock = flexmock(six.moves.builtins)
        mock.should_call('__import__')

        mock.should_receive('__import__')
        assert self.ypm.works()
        mock.should_receive('__import__').and_raise(ImportError)
        assert not self.ypm.works()

    @pytest.mark.parametrize(('correct_query', 'wrong_query', 'string', 'expected'), [
        ('group', 'rpm', '@foo', True),
        ('rpm', 'group', 'foo', True),
        ('group', 'rpm', '@foo', False),
        ('rpm', 'group', 'foo', False),
    ])
    def test_is_pkg_installed(self, correct_query, wrong_query, string, expected):
        correct_method = 'is_{query}_installed'.format(query=correct_query)
        wrong_method = 'is_{query}_installed'.format(query=wrong_query)
        flexmock(self.ypm)
        self.ypm.should_receive(correct_method).and_return(expected).at_least().once()
        self.ypm.should_call(wrong_method).never()
        assert self.ypm.is_pkg_installed(string) is expected

    @pytest.mark.skipif(module_not_available('yum'), reason='Requires yum module')
    def test_resolve(self):
        import yum
        expected = ['bar', 'baz']
        fake_pkgs = [flexmock(po=flexmock(ui_envra=name)) for name in expected]
        fake_yumbase = flexmock(setCacheDir=lambda x: True,
                                selectGroup=lambda x: True,
                                install=lambda x: True,
                                returnPackageByDep=lambda x: True,
                                resolveDeps=lambda: True,
                                tsInfo=flexmock(getMembers=lambda: fake_pkgs))
        flexmock(yum.YumBase).new_instances(fake_yumbase)
        assert self.ypm.resolve('foo') == expected
        fake_yumbase.should_receive('resolveDeps').and_raise(yum.Errors.PackageSackError)
        with pytest.raises(DependencyException):
            self.ypm.resolve('foo')


class TestDNFPackageManager(object):

    def setup_method(self, method):
        self.dpm = package_managers.DNFPackageManager

    @pytest.mark.parametrize(('group', 'output', 'result'), [
        ('foo', 'Installed Groups', 'foo'),
        ('bar', '', False)
    ])
    def test_is_group_installed(self, group, output, result):
        flexmock(ClHelper).should_receive('run_command')\
                .with_args('dnf groups list "{grp}"'.format(grp=group)).and_return(output)
        cmd_result = self.dpm.is_group_installed(group)
        assert cmd_result == result

    def test_install(self):
        pkgs = ('foo', 'bar', 'baz')

        flexmock(ClHelper).should_receive('run_command')
        assert self.dpm.install(*pkgs) == pkgs

        flexmock(ClHelper).should_receive('run_command').and_raise(ClException(None, None, None))
        assert self.dpm.install(*pkgs) is False

    def test_works(self):
        mock = flexmock(six.moves.builtins)
        mock.should_call('__import__')

        mock.should_receive('__import__')
        assert self.dpm.works()
        mock.should_receive('__import__').and_raise(ImportError)
        assert not self.dpm.works()

    @pytest.mark.parametrize(('correct_query', 'wrong_query', 'string', 'expected'), [
        ('group', 'rpm', '@foo', True),
        ('rpm', 'group', 'foo', True),
        ('group', 'rpm', '@foo', False),
        ('rpm', 'group', 'foo', False),
    ])
    def test_is_pkg_installed(self, correct_query, wrong_query, string, expected):
        correct_method = 'is_{query}_installed'.format(query=correct_query)
        wrong_method = 'is_{query}_installed'.format(query=wrong_query)
        flexmock(self.dpm)
        self.dpm.should_receive(correct_method).and_return(expected).at_least().once()
        self.dpm.should_call(wrong_method).never()
        assert self.dpm.is_pkg_installed(string) is expected

    @pytest.mark.skipif(module_not_available('dnf'), reason='Requires dnf module')
    def test_resolve(self):
        import dnf
        expected = ['bar', 'baz']
        fake_sack = flexmock()
        fake_sack.should_receive('query.available.filter.run').and_return(expected)
        fake_dnfbase = flexmock(conf=flexmock(cachedir='', substitutions={}),
                                sack=fake_sack,
                                fill_sack=lambda *args, **kwargs: None,
                                read_all_repos=lambda: None,
                                install=lambda x: True,
                                resolve=lambda: None,
                                transaction=flexmock(install_set=expected))
        flexmock(dnf.Base).new_instances(fake_dnfbase)
        assert self.dpm.resolve('foo') == expected
        fake_dnfbase.should_receive('resolve').and_raise(dnf.exceptions.Error)
        with pytest.raises(DependencyException):
            self.dpm.resolve('foo')


class TestPacmanPackageManager(object):

    def setup_class(self):
        self.ppm = package_managers.PacmanPackageManager

    def test_install(self):
        pkgs = ('foo', 'bar')
        flexmock(ClHelper).should_receive('run_command')\
                          .with_args('pacman -S --noconfirm "foo" "bar"',\
                                     ignore_sigint=True, as_user='root').at_least().once()
        assert self.ppm.install(*pkgs) == pkgs

        flexmock(ClHelper).should_receive('run_command').and_raise(ClException(None, None, None))
        assert not self.ppm.install(*pkgs)

    def test_is_pacmanpkg_installed(self):
        pkg = 'foo'
        flexmock(ClHelper).should_receive('run_command')\
                          .with_args('pacman -Q "{pkg}"'.format(pkg=pkg))\
                          .and_return(pkg).at_least().once()
        assert self.ppm.is_pacmanpkg_installed(pkg) == 'foo'

        flexmock(ClHelper).should_receive('run_command').and_raise(ClException(None, None, None))
        assert not self.ppm.is_pacmanpkg_installed(pkg)

    def test_is_group_installed(self):
        group = 'foo'
        flexmock(ClHelper).should_receive('run_command')\
                          .with_args('pacman -Qg "{group}"'.format(group=group))\
                          .and_return(group).at_least().once()
        assert self.ppm.is_group_installed(group) == 'foo'

        flexmock(ClHelper).should_receive('run_command').and_raise(ClException(None, None, None))
        assert not self.ppm.is_group_installed(group)

    def test_works(self):
        flexmock(ClHelper).should_receive('run_command')\
                          .with_args('which pacman').at_least().once()
        assert self.ppm.works()

        flexmock(ClHelper).should_receive('run_command').and_raise(ClException(None, None, None))
        assert not self.ppm.works()

    def test_is_pkg_installed(self):
        flexmock(self.ppm)
        self.ppm.should_receive('is_group_installed').and_return(False)
        self.ppm.should_receive('is_pacmanpkg_installed').and_return(True).at_least().once()
        assert self.ppm.is_pkg_installed('foo')

        self.ppm.should_receive('is_pacmanpkg_installed').and_return(False)
        self.ppm.should_receive('is_group_installed').and_return(True).at_least().once()
        assert self.ppm.is_pkg_installed('foo')

        self.ppm.should_receive('is_pacmanpkg_installed').and_return(False)
        self.ppm.should_receive('is_group_installed').and_return(False)
        assert not self.ppm.is_pkg_installed('foo')

    def test_resolve(self):
        pass


class TestHomebrewPackageManager(object):

    def setup_class(self):
        self.hpm = package_managers.HomebrewPackageManager

    def test_install(self):
        pkgs = ('foo', 'bar')
        flexmock(ClHelper).should_receive('run_command')\
                          .with_args('brew install "foo" "bar"',\
                                     ignore_sigint=True).at_least().once()
        assert self.hpm.install(*pkgs) == pkgs

        flexmock(ClHelper).should_receive('run_command').and_raise(ClException(None, None, None))
        assert not self.hpm.install(*pkgs)

    def test_is_pkg_installed(self):
        flexmock(ClHelper).should_receive('run_command').with_args('brew list').and_return('foo\nbar')

        assert self.hpm.is_pkg_installed('foo')
        assert not self.hpm.is_pkg_installed('baz')

    @pytest.mark.parametrize(('pkg', 'expected'), [('foo', True), ('bar', True), ('baz', False)])
    def test_is_pkg_installed_with_fake(self, pkg, expected):
        try:
            setattr(self.hpm, '_installed', ['foo', 'bar'])

            assert self.hpm.is_pkg_installed(pkg) is expected
        except Exception as e:
            raise e
        finally:
            delattr(self.hpm, '_installed')

    def test_works(self):
        flexmock(ClHelper).should_receive('run_command')\
                          .with_args('which brew').at_least().once()
        assert self.hpm.works()

        flexmock(ClHelper).should_receive('run_command').and_raise(ClException(None, None, None))
        assert not self.hpm.works()

    # TODO add test case for empty pkg list
    @pytest.mark.parametrize(('pkgs', 'deps', 'more_deps'), [
        (['foo'], ['bar', 'baz'], []),
        (['foo', 'bar'], ['baz', 'foobar'], ['foobarbaz'])
    ])
    def test_resolve(self, pkgs, deps, more_deps):
        flexmock(ClHelper).should_receive('run_command')\
                .and_return('\n'.join(deps)).and_return('\n'.join(more_deps))

        assert set(self.hpm.resolve(*pkgs)) == set(deps + more_deps)


class TestPIPPackageManager(object):

    def setup_class(self):
        self.ppm = package_managers.PIPPackageManager

    def test_install(self):
        pkgs = ('foo', 'bar')
        flexmock(ClHelper).should_receive('run_command')\
                          .with_args('pip install --user "foo" "bar"',\
                                     ignore_sigint=True).at_least().once()
        assert self.ppm.install(*pkgs) == pkgs

        flexmock(ClHelper).should_receive('run_command').and_raise(ClException(None, None, None))
        assert not self.ppm.install(*pkgs)

    def test_works(self):
        flexmock(ClHelper).should_receive('run_command')\
                          .with_args('pip').at_least().once()
        assert self.ppm.works()

        flexmock(ClHelper).should_receive('run_command').and_raise(ClException(None, None, None))
        assert not self.ppm.works()

    def test_is_pkg_installed(self):
        flexmock(ClHelper).should_receive('run_command').with_args('pip list').and_return('foo (1)\nbar (2)')

        assert self.ppm.is_pkg_installed('foo')
        assert not self.ppm.is_pkg_installed('baz')

    @pytest.mark.parametrize(('pkg', 'expected'), [('foo', True), ('bar', True), ('baz', False)])
    def test_is_pkg_installed_with_fake(self, pkg, expected):
        try:
            setattr(self.ppm, '_installed', ['foo (1)', 'bar (2)'])

            assert self.ppm.is_pkg_installed(pkg) is expected
        finally:
            delattr(self.ppm, '_installed')

    def test_resolve(self):
        pkgs = ('foo', 'bar', 'baz')
        assert self.ppm.resolve(*pkgs) == pkgs

    def test_get_distro_dependencies(self):
        pass


class TestNPMPackageManager(object):

    def setup_class(self):
        self.npm = package_managers.NPMPackageManager

    def test_install(self):
        pkgs = ('foo', 'bar')
        flexmock(ClHelper).should_receive('run_command')\
                          .with_args('npm install "foo" "bar"',\
                                     ignore_sigint=True).at_least().once()
        assert self.npm.install(*pkgs) == pkgs

        flexmock(ClHelper).should_receive('run_command').and_raise(ClException(None, None, None))
        assert not self.npm.install(*pkgs)

    def test_works(self):
        flexmock(ClHelper).should_receive('run_command')\
                          .with_args('npm').at_least().once()
        assert self.npm.works()

        flexmock(ClHelper).should_receive('run_command').and_raise(ClException(None, None, None))
        assert not self.npm.works()

    def test_is_pkg_installed(self):
        flexmock(ClHelper).should_receive('run_command').with_args('npm list').and_return('foo (1)\nbar (2)')

        assert self.npm.is_pkg_installed('foo')
        assert not self.npm.is_pkg_installed('baz')

    @pytest.mark.parametrize(('pkg', 'expected'), [('foo', True), ('bar', True), ('baz', False)])
    def test_is_pkg_installed_with_fake(self, pkg, expected):
        try:
            setattr(self.npm, '_installed', ['foo (1)', 'bar (2)'])

            assert self.npm.is_pkg_installed(pkg) is expected
        finally:
            delattr(self.npm, '_installed')

    def test_resolve(self):
        pkgs = ('foo', 'bar', 'baz')
        assert self.npm.resolve(*pkgs) == tuple(pkgs)

    def test_get_distro_dependencies(self):
        pass


class TestGemPackageManager(object):

    def setup_class(self):
        self.gpm = package_managers.GemPackageManager

    def test_install(self):
        pkgs = ('foo', 'bar')
        flexmock(ClHelper).should_receive('run_command')\
                          .with_args('gem install "foo" "bar"',\
                                     ignore_sigint=True).at_least().once()
        assert self.gpm.install(*pkgs) == pkgs

        flexmock(ClHelper).should_receive('run_command').and_raise(ClException(None, None, None))
        assert not self.gpm.install(*pkgs)

    def test_works(self):
        flexmock(ClHelper).should_receive('run_command')\
                          .with_args('which gem').at_least().once()
        assert self.gpm.works()

        flexmock(ClHelper).should_receive('run_command').and_raise(ClException(None, None, None))
        assert not self.gpm.works()

    def test_is_pkg_installed(self):
        flexmock(ClHelper).should_receive('run_command')\
                          .with_args('gem list -i "foo"')
        assert self.gpm.is_pkg_installed('foo')

        flexmock(ClHelper).should_receive('run_command')\
                          .and_raise(ClException(None, None, None))
        assert not self.gpm.is_pkg_installed('baz')

    def test_resolve(self):
        pkgs = ('foo', 'bar', 'baz')
        assert self.gpm.resolve(*pkgs) == tuple(pkgs)

    def test_get_distro_dependencies(self):
        pass


class TestGentooPackageManager(object):

    def setup_class(self):
        self.gpm = package_managers.GentooPackageManager

    def teardown_method(self, method):
        try:
            delattr(self.gpm, 'works_result')
        except:
            pass

    def test_const(self):
        assert self.gpm.PORTAGE == 0
        assert self.gpm.PALUDIS == 1

    def test_try_get_current_manager_fails(self):
        flexmock(utils).should_receive('get_distro_name.find').with_args('gentoo').and_return(-1)
        assert self.gpm._try_get_current_manager() is None

        flexmock(utils).should_receive('get_distro_name.find').with_args('gentoo').and_return(0)
        flexmock(os).should_receive('environ').and_return({'PACKAGE_MANAGER': 'foo'})
        assert self.gpm._try_get_current_manager() is None

    @pytest.mark.parametrize(('manager', 'man_val'), [
        ('paludis', package_managers.GentooPackageManager.PALUDIS),
        ('portage', package_managers.GentooPackageManager.PORTAGE),
    ])
    def test_try_get_current_manager(self, manager, man_val):
        flexmock(utils).should_receive('get_distro_name.find').with_args('gentoo').and_return(0)
        mock = flexmock(six.moves.builtins)

        flexmock(os).should_receive('environ').and_return({'PACKAGE_MANAGER': manager})
        mock.should_receive('__import__')
        assert self.gpm._try_get_current_manager() == man_val

        mock.should_receive('__import__').and_raise(ImportError)
        assert self.gpm._try_get_current_manager() is None

    @pytest.mark.parametrize('manager', [
        package_managers.GentooPackageManager.PALUDIS,
        package_managers.GentooPackageManager.PORTAGE,
        'foo'
        ])
    def test_is_current_manager_equals_to(self, manager):
        flexmock(self.gpm).should_receive('_try_get_current_manager').and_return(manager)
        assert self.gpm.is_current_manager_equals_to(manager) is True
        assert hasattr(self.gpm, 'works_result')

    def test_throw_package_list(self):
        with pytest.raises(AssertionError):
            self.gpm.throw_package_list(dict())

        with pytest.raises(DependencyException) as e:
            self.gpm.throw_package_list(['foo', 'bar'])
        msg = str(e)
        assert 'foo' in msg and 'bar' in msg


class TestEmergePackageManager(object):

    def setup_class(self):
        self.epm = package_managers.EmergePackageManager

    def teardown_method(self, method):
        try:
            delattr(self.epm, 'works_result')
        except:
            pass

    def test_install(self):
        pass

    def test_works(self):
        flexmock(self.epm).should_receive('_try_get_current_manager')\
                          .and_return(self.epm.PORTAGE)
        assert self.epm.works()

    @pytest.mark.parametrize('manager', [
        package_managers.GentooPackageManager.PALUDIS,
        None
        ])
    def test_not_works(self, manager):
        flexmock(self.epm).should_receive('_try_get_current_manager').and_return(manager)
        assert not self.epm.works()

    def test_is_pkg_installed(self):
        fake_vartree = flexmock(dbapi=flexmock(match=lambda x: {'foo': 'foobar',
                                                                'bar': None}[x]))
        fake_portage = flexmock(root='/', db={'/': {'vartree': fake_vartree}},
                                exception=flexmock(InvalidAtom=Exception))
        flexmock(six.moves.builtins).should_receive('__import__').and_return(fake_portage)

        assert self.epm.is_pkg_installed('foo')
        assert not self.epm.is_pkg_installed('bar')

        # Wrong Atom format
        flexmock(fake_vartree.dbapi.should_receive('match')\
                                   .and_raise(fake_portage.exception.InvalidAtom()))
        with pytest.raises(DependencyException) as e:
            self.epm.is_pkg_installed('bar')
        msg = str(e)
        assert 'bar' in msg and 'Invalid dependency' in msg

    def test_resolve(self):
        fake_porttree = flexmock(dep_bestmatch=lambda x: '{x}bar'.format(x=x))
        fake_portage = flexmock(root='/', db={'/': {'porttree': fake_porttree}})
        flexmock(six.moves.builtins).should_receive('__import__').and_return(fake_portage)

        with pytest.raises(DependencyException) as e:
            self.epm.resolve('foo')
        msg = str(e)
        assert 'foobar' in msg and 'Package not found' not in msg

        with pytest.raises(DependencyException) as e:
            assert self.epm.resolve('foo', 'bar')
        msg = str(e)
        assert 'foo' in msg and 'bar' in msg and 'Package not found' not in msg


class TestPaludisPackageManager(object):

    def setup_class(self):
        self.ppm = package_managers.PaludisPackageManager

    def teardown_method(self, method):
        try:
            delattr(self.ppm, 'works_result')
        except:
            pass

    def test_install(self):
        pass

    def test_works(self):
        flexmock(self.ppm).should_receive('_try_get_current_manager')\
                          .and_return(self.ppm.PALUDIS)
        assert self.ppm.works()

    @pytest.mark.parametrize('manager', [
        package_managers.GentooPackageManager.PORTAGE,
        None
        ])
    def test_not_works(self, manager):
        flexmock(self.ppm).should_receive('_try_get_current_manager').and_return(manager)
        assert not self.ppm.works()

    @pytest.mark.parametrize(('pkg', 'installed'), [
        ('foo', ['foo', 'bar']),
        ('baz', ['foo', 'bar']),
        ('foo', [])
    ])
    def test_is_pkg_installed(self, pkg, installed):
        fake_paludis = flexmock(BaseException=Exception,
                                EnvironmentFactory=flexmock(instance=\
                                    flexmock(create=lambda x: fake_env)),
                                parse_user_package_dep_spec=lambda x,y,z: fake_pkg,
                                UserPackageDepSpecOptions=lambda: None)
        fake_env = flexmock(fetch_repository=lambda x: {'installed': fake_repo}[x])
        fake_repo = flexmock(package_ids=lambda x, y: [x] if x else y)
        fake_pkg = flexmock(package=pkg if pkg in installed else '')
        flexmock(six.moves.builtins).should_receive('__import__').and_return(fake_paludis)

        if pkg in installed:
            assert self.ppm.is_pkg_installed('pkg') == [pkg]
        else:
            assert self.ppm.is_pkg_installed('pkg') == []

    def test_resolve(self):
        # TODO write test for resolution
        pass


class TestDependencyInstaller(object):

    def setup_method(self, method):
        self.di = package_managers.DependencyInstaller()

    def test_get_package_manager(self):
        # also mock __name__ for package managers, since they're supposed to be classes
        non_working_mgr = flexmock(works=lambda: False, __name__='non_working_mgr')
        working_mgr = flexmock(works=lambda: True, __name__='working_mgr')
        flexmock(package_managers).should_receive('managers')\
                                  .and_return({'foo': [non_working_mgr, working_mgr],
                                               'bar': [non_working_mgr],
                                               'baz': []})

        assert self.di.get_package_manager('foo') == working_mgr
        with pytest.raises(NoPackageManagerOperationalException):
            self.di.get_package_manager('bar')
        with pytest.raises(NoPackageManagerException):
            self.di.get_package_manager('baz')
        with pytest.raises(NoPackageManagerException):
            self.di.get_package_manager('foobar')

    def test_process_dependency_fails(self):
        flexmock(package_managers).should_receive('managers')\
                                  .and_return({'foomgr': []})

        with pytest.raises(NoPackageManagerException):
            self.di._process_dependency('barmgr', [])

    def test_process_dependency_distro(self):
        flexmock(package_managers).should_receive('managers')\
                                  .and_return({'foomgr': []})
        flexmock(settings, SYSTEM_DEPTYPES_SHORTCUTS={'foomgr': ['foodistro'],
                                                      'barmgr': ['bardistro']})
        flexmock(utils, get_distro_name=lambda: 'foodistro')

        self.di._process_dependency('foomgr', ['bar'])
        assert self.di.dependencies == [('foomgr', ['bar'])]

    def test_process_dependency_non_distro(self):
        foomgr = flexmock(get_distro_dependencies=lambda x: ['bar'])
        flexmock(package_managers).should_receive('managers')\
                                  .and_return({'foomgr': [foomgr], 'barmgr': []})
        flexmock(settings, SYSTEM_DEPTYPES_SHORTCUTS={'barmgr': ['foodistro']})
        flexmock(utils, get_distro_name=lambda: 'foodistro')
        flexmock(self.di, get_system_deptype_shortcut=lambda: 'barmgr')

        self.di._process_dependency('foomgr', ['bar', 'baz'])
        assert self.di.dependencies == [('barmgr', ['bar']), ('foomgr', ['bar', 'baz'])]

    @pytest.mark.parametrize('val', [True, False])
    def test_ask_to_confirm(self, val):
        pkg_list = ('foo', 'bar')
        fake_mgr = flexmock(get_perm_prompt=lambda x: 'Foobar: {0}'.format(' '.join(x)))
        flexmock(DialogHelper).should_receive('ask_for_package_list_confirm')\
                              .with_args('cli', prompt=str, package_list=pkg_list)\
                              .and_return('\n'.join(pkg_list) if val else None)

        assert self.di._ask_to_confirm('cli', fake_mgr, *pkg_list) is val

    def test_install_dependencies_empty(self):
        self.di.dependencies = [('foomgr', [])]
        flexmock(self.di).should_call('get_package_manager').never()

        self.di._install_dependencies(ui='cli', debug=False)

    def test_install_dependencies_already_installed(self):
        self.di.dependencies = [('foomgr', ['foo', 'bar'])]
        pkg_mgr = flexmock(works=lambda: True, is_pkg_installed=lambda x: True,
                           resolve=lambda x: None)
        flexmock(package_managers).should_receive('managers')\
                                  .and_return({'foomgr': [pkg_mgr]})
        flexmock(pkg_mgr).should_call('resolve').never()

        self.di._install_dependencies(ui='cli', debug=False)

    def test_install_dependencies_denied(self):
        self.di.dependencies = [('foomgr', ['foo', 'bar'])]
        pkg_mgr = flexmock(works=lambda: True, is_pkg_installed=lambda x: False)
        pkg_mgr.should_receive('resolve').and_return(['foo', 'bar', 'baz'])
        flexmock(package_managers).should_receive('managers')\
                                  .and_return({'foomgr': [pkg_mgr]})
        flexmock(self.di).should_receive('_ask_to_confirm')\
                        .with_args('cli', object, *['foo', 'bar', 'baz']).and_return(False)
        with pytest.raises(DependencyException):
            self.di._install_dependencies(ui='cli', debug=False)

    @pytest.mark.parametrize('ui', ['cli', 'foo'])
    def test_install_dependencies(self, ui):
        self.di.dependencies = [('foomgr', ['foo', 'bar'])]
        pkg_mgr = flexmock(works=lambda: True, is_pkg_installed=lambda x: False)
        pkg_mgr.should_receive('resolve').and_return(['foo', 'bar', 'baz'])
        flexmock(package_managers).should_receive('managers')\
                                  .and_return({'foomgr': [pkg_mgr]})
        flexmock(self.di).should_receive('_ask_to_confirm')\
                        .with_args(ui, object, *['foo', 'bar', 'baz']).and_return(True)

        # Successful run
        pkg_mgr.should_receive('install').with_args('foo', 'bar', 'baz')\
               .and_return(('foo', 'bar', 'baz')).at_least().once()
        self.di._install_dependencies(ui=ui, debug=False)

        # Unsuccessful run
        pkg_mgr.should_receive('install').with_args('foo', 'bar', 'baz')\
               .and_return(False).at_least().once()
        with pytest.raises(DependencyException):
            self.di._install_dependencies(ui=ui, debug=False)

    @pytest.mark.parametrize(('distro', 'dep_t'), [
        ('foodistro', 'foomgr'),
        ('bardistro', 'barmgr'),
        ('bazdistro', 'rpm')
    ])
    def test_get_system_deptype_shortcut(self, distro, dep_t):
        flexmock(utils).should_receive('get_distro_name').and_return(distro)
        flexmock(settings, SYSTEM_DEPTYPES_SHORTCUTS={'foomgr': ['foodistro'],
                                                      'barmgr': ['bardistro']})
        assert self.di.get_system_deptype_shortcut() == dep_t
