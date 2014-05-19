import pytest
import six

from flexmock import flexmock

from devassistant.exceptions import ClException, DependencyException
from devassistant.command_helpers import ClHelper
from devassistant.package_managers import YUMPackageManager, PacmanPackageManager,\
                                          HomebrewPackageManager, PIPPackageManager

def yum_not_available():
    try:
        import yum
        return False
    except ImportError:
        return True

class TestYUMPackageManager(object):

    def setup_method(self, method):
        self.ypm = YUMPackageManager

    @pytest.mark.parametrize('result', [True, False])
    def test_is_rpm_installed(self, result):
        flexmock(ClHelper).should_receive('run_command')\
                .with_args('rpm -q --whatprovides "foo"').and_return(result)
        assert self.ypm.is_rpm_installed('foo') is result

    @pytest.mark.parametrize(('group', 'output', 'result'), [
        ('foo', 'Installed Groups', 'foo'),
        ('bar', '', False)
    ])
    def test_is_group_installed(self, group, output, result):
        flexmock(ClHelper).should_receive('run_command')\
                .with_args('yum group list "{grp}"'.format(grp=group)).and_return(output)
        assert self.ypm.is_group_installed(group) == result

    def test_was_rpm_installed(self):
        pass

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

    @pytest.mark.skipif(yum_not_available(), reason='Requires yum module')
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

class TestPacmanPackageManager(object):

    def setup_class(self):
        self.ppm = PacmanPackageManager

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
        self.hpm = HomebrewPackageManager

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
        self.ppm = PIPPackageManager

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
            print(self.ppm.is_pkg_installed(pkg))

            assert self.ppm.is_pkg_installed(pkg) is expected
        finally:
            delattr(self.ppm, '_installed')

    def test_resolve(self):
        pkgs = ['a', 'b', 'c']
        assert self.ppm.resolve(pkgs) == pkgs

    def test_get_distro_dependencies(self):
        pass
