# -*- coding: utf-8 -*-
"""General notes on dependency installation:
The only class that should be used from outside is DependencyInstaller. It uses PackageManager
subclasses to install dependencies collected from assistants/snippets, e.g.
[{'rpm': ['package1', 'package2'], 'pip': ['spam']}, {'gem': ['foo']}]

DevAssistant distinguishes two general types of dependencies:
- system dependencies (rpm, pacman, ...)
- non-system dependencies

System dependencies are special, since DependencyInstaller throws away all system
dependencies that are not native to this system. E.g. it throws away RPM deps on
ArchLinux. Non-system dependencies are always processed, since they should be
distro-agnostic.

PackageManager subclasses represent the tools that are used to install the dependencies.
Note, that sometimes there isn't 1:1 mapping from dependency types to package managers -
RPM, for example, is handled by YUM on Fedora, but there are different tools
on other platforms, e.g. Zypper on OpenSuse. PackageManager subclasses should always
represent these high-level tools like YUM or Zypper, not RPM itself.
"""
from __future__ import print_function
import math
import os
import platform
import sys
import tempfile
import time
import threading

from devassistant.command_helpers import ClHelper, DialogHelper
from devassistant.logger import logger
from devassistant import exceptions
from devassistant import utils
from devassistant import settings

# mapping of dependency types to managers that handle them
# e.g. {'rpm': [YUMPackageManager, DNFPackageManager],
#       'pip': [PIPPackageManager]}
managers = {}


def register_manager(manager):
    managers.setdefault(manager.shortcut, [])
    managers[manager.shortcut].append(manager)
    return manager


class PackageManager(object):
    """Abstract class for API definition of package managers."""

    # Indicates whether this is a system manager.
    is_system = True

    @classmethod
    def get_perm_prompt(cls, package_list):
        """
        Return text for prompt (do you want to install...), to install given packages.
        """
        if cls == PackageManager:
            raise NotImplementedError()
        ln = len(package_list)
        plural = 's' if ln > 1 else ''
        return cls.permission_prompt.format(num=ln, plural=plural)

    @classmethod
    def install(cls, *args, **kwargs):
        """Install dependency.

        Note: if you want your dependency installation to be uninterruptible, pass
        ignore_sigint=True to ClHelper.run_command.
        """
        raise NotImplementedError()

    @classmethod
    def works(cls, *args, **kwargs):
        """Returns True if this package manager is usable, False otherwise."""
        raise NotImplementedError()

    @classmethod
    def is_pkg_installed(cls, *args, **kwargs):
        """Is a package managed by this manager installed?"""
        raise NotImplementedError()

    @classmethod
    def resolve(cls, *args, **kwargs):
        """
        Return all dependencies which will be installed. Problem here is that
        not all package managers could support this.
        """
        raise NotImplementedError()

    @classmethod
    def get_distro_dependencies(cls, smgr_sc):
        """
        Return dependencies needed for this non-system manager to work.
        Args:
            smgr_sc: shortcut of system manager to return dependencies for
        Returns:
            list of dependencies that are to be installed via given system dependency manager
            in order for this manager to work
        Raises:
            NotImplementedError: if this manager is system manager (makes no sense to call this)
        """
        raise NotImplementedError()

    @classmethod
    def _debug_doesnt_work(cls, msg, name=None):
        logger.debug('{0} not operational - {1}'.format(name or cls.__name__, msg))


class RPMPackageManager(PackageManager):

    shortcut = 'rpm'
    c_rpm = 'rpm'

    @classmethod
    def rpm_q(cls, rpm_name):
        try:
            # if we install by e.g. virtual provide, then rpm -q foo will fail
            # therefore we always use rpm -q --whatprovides foo
            return ClHelper.run_command(' '.join([cls.c_rpm,
                                                  '-q',
                                                  '--whatprovides',
                                                  '"' + rpm_name.strip() + '"']))
        except exceptions.ClException:
            return False

    @classmethod
    def is_rpm_installed(cls, rpm_name):
        logger.info('Checking for presence of {0}...'.format(rpm_name),
                    extra={'event_type': 'dep_check'})

        found_rpm = cls.rpm_q(rpm_name)
        if found_rpm:
            logger.info('Found {0}'.format(found_rpm), extra={'event_type': 'dep_found'})
        else:
            logger.info('Not found, will install', extra={'event_type': 'dep_not_found'})
        return found_rpm


@register_manager
class YUMPackageManager(RPMPackageManager):
    """Package manager for managing rpm packages from repositories by Yum.
    TODO: when we start using another RPM platform with another installer (OpenSuse),
    we will need to pull out the RPM stuff into common superclass."""
    permission_prompt = "Installing {num} RPM package{plural} by Yum. Is this ok?"

    c_yum = 'yum'

    @classmethod
    def is_group_installed(cls, group):
        logger.info('Checking for presence of group {0}...'.format(group))

        output = ClHelper.run_command(' '.join(
            [cls.c_yum, 'group', 'list', '"{0}"'.format(group)]))
        if 'Installed Groups' in output:
            logger.info('Found {0}'.format(group), extra={'event_type': 'dep_found'})
            return group
        else:
            logger.info('Not found, will install', extra={'event_type': 'dep_not_found'})
        return False

    @classmethod
    def install(cls, *args):
        cmd = [cls.c_yum, '-y', 'install']
        quoted_pkgs = map(lambda pkg: '"{pkg}"'.format(pkg=pkg), args)
        cmd.extend(quoted_pkgs)
        try:
            ClHelper.run_command(' '.join(cmd), ignore_sigint=True, as_user='root')
            return args
        except exceptions.ClException:
            return False

    @classmethod
    def works(cls):
        try:
            import yum
            return True
        except ImportError:
            cls._debug_doesnt_work('can\'t import yum.')
            return False

    @classmethod
    def is_pkg_installed(cls, pkg):
        return cls.is_group_installed(pkg) if pkg.startswith('@') else cls.is_rpm_installed(pkg)

    @classmethod
    def resolve(cls, *args):
        logger.info('Resolving RPM dependencies ...')
        import yum
        y = yum.YumBase()
        y.setCacheDir(tempfile.mkdtemp())
        for pkg in args:
            if pkg.startswith('@'):
                y.selectGroup(pkg[1:])
            else:
                try:
                    y.install(y.returnPackageByDep(pkg))
                except yum.Errors.YumBaseError:
                    msg = 'Package not found: {pkg}'.format(pkg=pkg)
                    raise exceptions.DependencyException(msg)
        try:
            y.resolveDeps()
        except yum.Errors.PackageSackError as e:  # Resolution of Issue 154
            raise exceptions.DependencyException('Error resolving RPM dependencies: {0}'.
                                                 format(utils.exc_as_decoded_string(e)))

        logger.debug('Installing/Updating:')
        to_install = []
        for pkg in y.tsInfo.getMembers():
            to_install.append(pkg.po.ui_envra)
            logger.debug(pkg.po.ui_envra)

        return to_install

    def __str__(self):
        return "YUM package manager"


@register_manager
class DNFPackageManager(RPMPackageManager):
    """Package manager for managing rpm packages from repositories by Yum.
    TODO: when we start using another RPM platform with another installer (OpenSuse),
    we will need to pull out the RPM stuff into common superclass."""
    permission_prompt = "Installing {num} RPM package{plural} with DNF. Is this ok?"

    c_dnf = 'dnf'

    @classmethod
    def is_group_installed(cls, group):
        logger.info('Checking for presence of group {0}...'.format(group))

        output = ClHelper.run_command(' '.join(
            [cls.c_dnf, 'groups', 'list', '"{0}"'.format(group)]))
        if 'installed groups' in output.lower():
            logger.info('Found {0}'.format(group), extra={'event_type': 'dep_found'})
            return group
        else:
            logger.info('Not found, will install', extra={'event_type': 'dep_not_found'})
        return False

    @classmethod
    def install(cls, *args):
        cmd = [cls.c_dnf, '-y', 'install']
        quoted_pkgs = map(lambda pkg: '"{pkg}"'.format(pkg=pkg), args)
        cmd.extend(quoted_pkgs)
        try:
            ClHelper.run_command(' '.join(cmd), ignore_sigint=True, as_user='root')
            return args
        except exceptions.ClException:
            return False

    @classmethod
    def works(cls):
        try:
            import dnf
            import hawkey
            return True
        except ImportError:
            cls._debug_doesnt_work('can\'t import dnf or hawkey.')
            return False

    @classmethod
    def is_pkg_installed(cls, pkg):
        return cls.is_group_installed(pkg) if pkg.startswith('@') else cls.is_rpm_installed(pkg)

    @classmethod
    def resolve(cls, *args):
        logger.info('Resolving RPM dependencies with DNF...')
        import dnf
        import hawkey
        base = dnf.Base()
        base.conf.cachedir = tempfile.mkdtemp()
        base.conf.substitutions['releasever'] = platform.linux_distribution()[1]
        base.read_all_repos()
        base.fill_sack(load_system_repo=True, load_available_repos=True)
        for pkg in (str(arg) for arg in args):
            if pkg.startswith('@'):
                base.group_install(pkg[1:])
            else:
                try:
                    res = base.sack.query().available().filter(provides=pkg).run()
                    base.install(str(res[0]))
                except (hawkey.QueryException, IndexError):
                    msg = 'Package not found: {pkg}'.format(pkg=pkg)
                    raise exceptions.DependencyException(msg)
        try:
            base.resolve()
        except dnf.exceptions.Error as e:
            raise exceptions.DependencyException('Error resolving RPM dependencies with DNF: {0}'.
                                                 format(utils.exc_as_decoded_string(e)))

        logger.debug('Installing/Updating:')
        to_install = []
        for pkg in base.transaction.install_set:
            to_install.append(str(pkg))
            logger.debug(str(pkg))

        return to_install

    def __str__(self):
        return "DNF package manager"


@register_manager
class PacmanPackageManager(PackageManager):
    """Package manager for managing Arch Linux packages by pacman."""
    permission_prompt = "Installing {num} package{plural} by Pacman. Is this ok?"
    shortcut = 'pacman'

    c_pacman = 'pacman'

    @classmethod
    def install(cls, *args):
        cmd = [cls.c_pacman, '-S', '--noconfirm']
        quoted_pkgs = map(lambda pkg: '"{pkg}"'.format(pkg=pkg), args)
        cmd.extend(quoted_pkgs)
        try:
            ClHelper.run_command(' '.join(cmd), ignore_sigint=True, as_user='root')
            return args
        except exceptions.ClException:
            return False

    @classmethod
    def is_pacmanpkg_installed(cls, pkg_name):
        logger.info('Checking for presence of {0}...'.format(pkg_name),
                    extra={'event_type': 'dep_check'})

        try:
            found_pkg = ClHelper.run_command('{pacman} -Q "{pkg}"'.
                                             format(pacman=cls.c_pacman, pkg=pkg_name))
            logger.info('Found {0}'.format(found_pkg), extra={'event_type': 'dep_found'})
            return found_pkg
        except exceptions.ClException:
            logger.info('Not found, will install', extra={'event_type': 'dep_not_found'})
            return False

    @classmethod
    def is_group_installed(cls, group):
        logger.info('Checking for presence of group {0}...'.format(group))

        try:
            ClHelper.run_command('{pacman} -Qg "{group}"'.
                                 format(pacman=cls.c_pacman,
                                        group=group))
            return group
        except exceptions.ClException:
            return False

    @classmethod
    def works(cls):
        try:
            ClHelper.run_command('which pacman')
            return True
        except exceptions.ClException:
            cls._debug_doesnt_work('"pacman" binary not found')
            return False

    @classmethod
    def is_pkg_installed(cls, pkg):
        return cls.is_pacmanpkg_installed(pkg) or cls.is_group_installed(pkg)

    @classmethod
    def resolve(cls, *args):
        # TODO: I currently see no way how to just resolve dependencies by pacman
        return args


@register_manager
class HomebrewPackageManager(PackageManager):
    """Package manager for managing OSX packages by homebrew."""
    permission_prompt = "Installing {num} package{plural} by Homebrew. Is this ok?"
    shortcut = 'homebrew'

    c_homebrew = 'brew'

    @classmethod
    def install(cls, *args):
        cmd = [cls.c_homebrew, 'install']
        quoted_pkgs = ['"{0}"'.format(pkg) for pkg in args]
        cmd.extend(quoted_pkgs)
        try:
            ClHelper.run_command(' '.join(cmd), ignore_sigint=True)
            return args
        except exceptions.ClException:
            return False

    @classmethod
    def is_pkg_installed(cls, dep):
        logger.info('Checking for presence of {0}...'.format(dep),
                    extra={'event_type': 'dep_check'})
        if not getattr(cls, '_installed', None):
            query = ClHelper.run_command(' '.join([cls.c_homebrew, 'list']))
            cls._installed = query.split('\n')
        search = [e for e in cls._installed if e.startswith(dep)]
        if search:
            logger.info('Found {0}'.format(search[0]), extra={'event_type': 'dep_found'})
        else:
            logger.info('Not found, will install', extra={'event_type': 'dep_not_found'})

        return len(search) > 0

    @classmethod
    def works(cls):
        try:
            ClHelper.run_command('which brew')
            return True
        except exceptions.ClException:
            cls._debug_doesnt_work('"brew" binary not found')
            return False

    @classmethod
    def resolve(cls, *args):
        logger.info('Resolving Homebrew dependencies ...')
        for pkg in args:
            logger.debug('Looking at {0}'.format(pkg))

        logger.debug('Installing/Updating:')
        to_install = set()
        for pkg in args:
            query = ClHelper.run_command(' '.join([cls.c_homebrew, 'deps -n', pkg]))
            to_install.update(query.split('\n'))

        return list(to_install)


@register_manager
class PIPPackageManager(PackageManager):
    """ Package manager for managing python dependencies from PyPI """
    permission_prompt = "Installing {num} package{plural} from PyPI. Is this ok?"
    shortcut = 'pip'
    is_system = False

    c_pip = 'pip'

    @classmethod
    def install(cls, *args):
        cmd = [cls.c_pip, 'install', '--user']
        quoted_pkgs = map(lambda pkg: '"{pkg}"'.format(pkg=pkg), args)
        cmd.extend(quoted_pkgs)
        try:
            ClHelper.run_command(' '.join(cmd), ignore_sigint=True)
            return args
        except exceptions.ClException:
            return False

    @classmethod
    def works(cls):
        try:
            ClHelper.run_command('pip')
            return True
        except exceptions.ClException:
            cls._debug_doesnt_work('"pip" binary not found')
            return False

    @classmethod
    def is_pkg_installed(cls, dep):
        logger.info('Checking for presence of {0}...'.format(dep),
                    extra={'event_type': 'dep_check'})
        if not getattr(cls, '_installed', None):
            query = ClHelper.run_command(' '.join([cls.c_pip, 'list']))
            cls._installed = query.split('\n')
        search = [e for e in cls._installed if e.startswith(dep + ' ')]
        if search:
            logger.info('Found {0}'.format(search[0]), extra={'event_type': 'dep_found'})
        else:
            logger.info('Not found, will install', extra={'event_type': 'dep_not_found'})

        return len(search) > 0

    @classmethod
    def resolve(cls, *dep):
        # depresolver for PyPI is infeasable to do -- there are no structured
        # metadata for python packages; so just return this dependency
        # PIPHelper.resolve(dep)
        logger.info('Resolving PyPI dependencies...')
        return dep

    @classmethod
    def get_distro_dependencies(self, smgr_sc):
        return ['python-pip']

    def __str__(self):
        return "pip package manager"


@register_manager
class NPMPackageManager(PackageManager):
    """ Package manager for managing python dependencies from NPM """
    permission_prompt = "Installing {num} package{plural} from NPM. Is this ok?"
    shortcut = 'npm'
    is_system = False

    c_npm = 'npm'

    @classmethod
    def install(cls, *args):
        cmd = [cls.c_npm, 'install']
        quoted_pkgs = map(lambda pkg: '"{pkg}"'.format(pkg=pkg), args)
        cmd.extend(quoted_pkgs)
        try:
            ClHelper.run_command(' '.join(cmd), ignore_sigint=True)
            return args
        except exceptions.ClException:
            return False

    @classmethod
    def works(cls):
        try:
            ClHelper.run_command('npm')
            return True
        except exceptions.ClException:
            cls._debug_doesnt_work('"npm" binary not found')
            return False

    @classmethod
    def is_pkg_installed(cls, dep):
        logger.info('Checking for presence of {0}...'.format(dep),
                    extra={'event_type': 'dep_check'})
        if not getattr(cls, '_installed', None):
            query = ClHelper.run_command(' '.join([cls.c_npm, 'list']))
            cls._installed = query.split('\n')
        search = [e for e in cls._installed if e.startswith(dep + ' ')]
        if search:
            logger.info('Found {0}'.format(search[0]), extra={'event_type': 'dep_found'})
        else:
            logger.info('Not found, will install', extra={'event_type': 'dep_not_found'})

        return len(search) > 0

    @classmethod
    def resolve(cls, *dep):
        logger.info('Resolving NPM dependencies...')
        return dep

    @classmethod
    def get_distro_dependencies(self, smgr_sc):
        return ['npm']

    def __str__(self):
        return "npm package manager"


@register_manager
class GemPackageManager(PackageManager):
    """ Package manager for managing ruby dependencies from rubygems.org """
    permission_prompt = "Installing {num} package{plural} from rubygems. Is this ok?"
    shortcut = 'gem'
    is_system = False

    c_gem = 'gem'

    @classmethod
    def install(cls, *args):
        cmd = [cls.c_gem, 'install']
        quoted_pkgs = map(lambda pkg: '"{pkg}"'.format(pkg=pkg), args)
        cmd.extend(quoted_pkgs)
        try:
            ClHelper.run_command(' '.join(cmd), ignore_sigint=True)
            return args
        except exceptions.ClException:
            return False

    @classmethod
    def works(cls):
        try:
            ClHelper.run_command('which gem')
            return True
        except exceptions.ClException:
            cls._debug_doesnt_work('"gem" binary not found')
            return False

    @classmethod
    def is_pkg_installed(cls, dep):
        logger.info('Checking for presence of {0}...'.format(dep),
                    extra={'event_type': 'dep_check'})
        try:
            ClHelper.run_command(' '.join([cls.c_gem, 'list', '-i', '"{pkg}"'.format(pkg=dep)]))
            logger.info('Found {0}'.format(dep), extra={'event_type': 'dep_found'})
            return True
        except exceptions.ClException:
            logger.info('Not found, will install', extra={'event_type': 'dep_not_found'})
            return False

    @classmethod
    def resolve(cls, *dep):
        logger.info('Resolving gem dependencies...')
        return dep

    @classmethod
    def get_distro_dependencies(self, smgr_sc):
        return ['rubygems', 'ruby-devel']

    def __str__(self):
        return "gem package manager"


class GentooPackageManager(PackageManager):
    """Mix-in class for Gentoo package managers. The only thing it capable to do
        is to detect current package manager used in a particular Gentoo based system.
    """
    PORTAGE = 0
    PALUDIS = 1

    @classmethod
    def _try_get_current_manager(cls):
        """ Try to detect a package manager used in a current Gentoo system. """
        if utils.get_distro_name().find('gentoo') == -1:
            return None
        if 'PACKAGE_MANAGER' in os.environ:
            pm = os.environ['PACKAGE_MANAGER']
            if pm == 'paludis':
                # Try to import paludis module
                try:
                    import paludis
                    return GentooPackageManager.PALUDIS
                except ImportError:
                    # TODO Environment tells that paludis must be used, but
                    # it seems latter was build w/o USE=python...
                    # Need to report an error!!??
                    cls._debug_doesnt_work('can\'t import paludis', name='PaludisPackageManager')
                    return None
            elif pm == 'portage':
                # Fallback to default: portage
                pass
            else:
                # ATTENTION Some unknown package manager?! Which one?
                return None

        # Try to import portage module
        try:
            import portage
            return GentooPackageManager.PORTAGE
        except ImportError:
            cls._debug_doesnt_work('can\'t import portage', name='EmergePackageManager')
            return None

    @classmethod
    def is_current_manager_equals_to(cls, pm):
        """Returns True if this package manager is usable, False otherwise."""
        if hasattr(cls, 'works_result'):
            return cls.works_result
        is_ok = bool(cls._try_get_current_manager() == pm)
        setattr(cls, 'works_result', is_ok)
        return is_ok

    @classmethod
    def throw_package_list(cls, to_install):
        assert(isinstance(to_install, list))
        _list = ', '.join(to_install)
        raise exceptions.DependencyException(
            'You must install the following packages before run this command: {0}'.format(_list)
        )


@register_manager
class EmergePackageManager(GentooPackageManager):
    """ Package manager class for Gentoo. It uses `emerge` underneath.

        ATTENTION Unfortunately in Gentoo it is not so easy to "just install" required
        dependencies. Partly because before compile anything user may wants to add/remove
        some USE flags to/from configs or maybe add some overlay to get access to required
        ebuild(s)... also, compiling from sources could takes a really long time (and a
        user possible just not ready to waste^W spent it right now).
        So, this "package" manager class wouldn't install anything!
        Instead it will just show to a user what packages must be installed...
    """

    shortcut = 'ebuild'

    @classmethod
    def install(cls, *args, **kwargs):
        raise NotImplementedError()

    @classmethod
    def works(cls, *args, **kwargs):
        """Returns True if this package manager is usable, False otherwise."""
        return cls.is_current_manager_equals_to(GentooPackageManager.PORTAGE)

    @classmethod
    def is_pkg_installed(cls, pkg):
        """Is a package managed by this manager installed?"""
        import portage
        # Get access to installed packages DB
        vartree = portage.db[portage.root]['vartree']
        try:
            r = vartree.dbapi.match(pkg)
            logger.debug('Checking is installed: {0} -> {1}'.format(pkg, repr(r)))
        except portage.exception.InvalidAtom:
            raise exceptions.DependencyException('Invalid dependency specification: {0}'.
                                                 format(pkg))
        # TODO Compare package version!
        return bool(r)

    @classmethod
    def resolve(cls, *deps):
        """
        Return all dependencies which will be installed.

        NOTE Simplified (naive) implementation will show the list of correctly
        spelled packages to be installed. For example 'firefox' will be resolved
        to 'www-client/firefox-25.0.1'...

        TODO ... or maybe version part must be stripped?
        """
        import portage

        logger.info('[portage] Resolving dependencies ...')

        porttree = portage.db[portage.root]['porttree']
        to_install = set()
        for dep in deps:
            res = porttree.dep_bestmatch(dep)
            logger.debug('{0} resolved to {1}'.format(repr(dep), repr(res)))
            if res:
                to_install.add(res)
            else:
                msg = 'Package not found or spec is invalid: {pkg}'.format(pkg=dep)
                raise exceptions.DependencyException(msg)

        cls.throw_package_list(list(to_install))


@register_manager
class PaludisPackageManager(GentooPackageManager):
    """Another package manager class for Gentoo (yep, for
    [paludis](http://paludis.exherbo.org/) ;-)

    NOTE Nowadays Paludis has Python2 only API, but Python3 is coming soon (I hope)
    (upstream bug is here http://paludis.exherbo.org/trac/ticket/1297).

    NOTE Ebuild for paludis w/ Python3 support available here:
    https://github.com/zaufi/zaufi-overlay/tree/master/sys-apps/paludis
    """

    shortcut = 'ebuild'

    @classmethod
    def install(cls, *args, **kwargs):
        raise NotImplementedError()

    @classmethod
    def works(cls, *args, **kwargs):
        """Returns True if this package manager is usable, False otherwise."""
        return cls.is_current_manager_equals_to(GentooPackageManager.PALUDIS)

    @classmethod
    def is_pkg_installed(cls, dep):
        """Is a package managed by this manager installed?"""
        import paludis
        env = paludis.EnvironmentFactory.instance.create('')
        installed = env.fetch_repository('installed')
        try:
            pkg = paludis.parse_user_package_dep_spec(dep, env,
                                                      paludis.UserPackageDepSpecOptions())
            # TODO Compare package version!
            r = []
            for i in installed.package_ids(str(pkg.package), []):
                r.append(str(i))
            logger.debug('Checking is installed: {0} -> {1}'.format(pkg, repr(r)))
            return r
        except paludis.BaseException as e:
            msg = 'Dependency specification is invalid [{0}]: {1}'.\
                format(dep, utils.exc_as_decoded_string(e))
            raise exceptions.DependencyException(msg)

    @classmethod
    def resolve(cls, *deps):
        """
        Return all dependencies which will be installed.
        Like a portage based implementation it just tries to get
        the best package available according a given spec.
        """
        import paludis

        logger.info('[paludis] Resolving dependencies ...')

        env = paludis.EnvironmentFactory.instance.create('')
        fltr = paludis.Filter.And(paludis.Filter.SupportsInstallAction(),
                                  paludis.Filter.NotMasked())
        to_install = set()
        for dep in deps:
            ds = paludis.parse_user_package_dep_spec(dep, env, paludis.UserPackageDepSpecOptions())
            gen = paludis.Generator.Matches(ds, paludis.MatchPackageOptions())
            fg = paludis.FilteredGenerator(gen, fltr)
            s = paludis.Selection.BestVersionOnly(fg)
            _to_install = set()
            for pkg in env[s]:
                _to_install.add(str(pkg))
            if _to_install:
                to_install += _to_install
            else:
                msg = 'Package not found: {pkg}'.format(pkg=dep)
                raise exceptions.DependencyException(msg)

        cls.throw_package_list(list(to_install))


class DependencyInstaller(object):
    """Installs all dependencies given to install() like this:
    - Calls _process_dependency for each dependency type, system dependencies always go first
      - "Implodes" the dependencies - e.g. if more 'rpm' lists were given, it creates one
        list of all of them
      - If it encounters system dependencies native for another system, it throws them away
      - For non-system dependency type (e.g. 'gem', 'pip'), it also adds a system dependency
        that has the ability to install these (e.g. rubygems, python-pip)
    - Calls _install_dependencies
      - For each dependency type
        - Gets proper manager to install it
        - Resolves dependencies of those dependencies :)
        - Installs the dependencies
    """
    # True if devassistant is installing dependencies and we can't interrupt the process
    install_lock = False

    """Class for installing dependencies """
    def __init__(self):
        # self.dependencies has form [(package_manager_shorcut, ['list', 'of', 'dependencies'])]
        #  previously, we used OrderedDict, but that's not in Python 2.6,
        #  so now we're using list of tuples
        #  we need to preserve the order that is used in assistants;
        #  we also want system dependencies to always go first
        self.dependencies = []

    def __add_dependencies(self, dep_t, dep_l):
        found = False
        for dt, dl in self.dependencies:
            if dep_t == dt:
                dl.extend(dep_l)
                found = True

        if not found:
            self.dependencies.append((dep_t, dep_l))

    def get_package_manager(self, dep_t):
        """Choose proper package manager and return it."""
        mgrs = managers.get(dep_t, [])
        for manager in mgrs:
            if manager.works():
                return manager
        if not mgrs:
            err = 'No package manager for dependency type "{dep_t}"'.format(dep_t=dep_t)
            raise exceptions.NoPackageManagerException(err)
        else:
            mgrs_nice = ', '.join([mgr.__name__ for mgr in mgrs])
            err = 'No working package manager for "{dep_t}" in: {mgrs}'.format(dep_t=dep_t,
                                                                              mgrs=mgrs_nice)
            raise exceptions.NoPackageManagerOperationalException(err)

    def _process_dependency(self, dep_t, dep_l):
        """Add dependencies into self.dependencies, possibly also adding system packages
        that contain non-distro package managers (e.g. if someone wants to install
        dependencies with pip and pip is not present, it will get installed through
        RPM on RPM based systems, etc.

        Skips dependencies that are supposed to be installed by system manager that
        is not native to this system.
        """
        if dep_t not in managers:
            err = 'No package manager for dependency type "{dep_t}"'.format(dep_t=dep_t)
            raise exceptions.NoPackageManagerException(err)
        # try to get list of distros where the dependency type is system type
        distros = settings.SYSTEM_DEPTYPES_SHORTCUTS.get(dep_t, None)
        if not distros:  # non-distro dependency type
            sysdep_t = self.get_system_deptype_shortcut()
            # for now, just take the first manager that can install dep_t and install this manager
            self._process_dependency(sysdep_t,
                                     managers[dep_t][0].get_distro_dependencies(sysdep_t))
        else:
            local_distro = utils.get_distro_name()
            found = False
            for distro in distros:
                if distro in local_distro:
                    found = True
                    break
            if not found:  # distro dependency type, but for another distro
                return
        self.__add_dependencies(dep_t, dep_l)

    def _ask_to_confirm(self, ui, pac_man, *to_install):
        """ Return True if user wants to install packages, False otherwise """
        ret = DialogHelper.ask_for_package_list_confirm(
            ui, prompt=pac_man.get_perm_prompt(to_install),
            package_list=to_install,
        )
        return bool(ret)

    def _install_dependencies(self, ui, debug):
        """Install missing dependencies"""
        for dep_t, dep_l in self.dependencies:
            if not dep_l:
                continue
            pkg_mgr = self.get_package_manager(dep_t)
            pkg_mgr.works()
            to_resolve = []
            for dep in dep_l:
                if not pkg_mgr.is_pkg_installed(dep):
                    to_resolve.append(dep)
            if not to_resolve:
                # nothing to install, let's move on
                continue
            to_install = pkg_mgr.resolve(*to_resolve)
            confirm = self._ask_to_confirm(ui, pkg_mgr, *to_install)
            if not confirm:
                msg = 'List of packages denied by user, exiting.'
                raise exceptions.DependencyException(msg)

            type(self).install_lock = True
            # TODO: we should do this more systematically (send signal to cl/gui?)
            logger.info('Installing dependencies, sit back and relax ...',
                        extra={'event_type': 'dep_installation_start'})
            if ui == 'cli' and not debug:  # TODO: maybe let every manager to decide when to start
                event = threading.Event()
                t = EndlessProgressThread(event)
                t.start()
            installed = pkg_mgr.install(*to_install)
            if ui == 'cli' and not debug:
                event.set()
                t.join()
                if installed:
                    logger.info(' Done.')
                else:
                    logger.error(' Failed.')
            type(self).install_lock = False

            log_extra = {'event_type': 'dep_installation_end'}
            if not installed:
                msg = 'Failed to install dependencies, exiting.'
                logger.error(msg, extra=log_extra)
                raise exceptions.DependencyException(msg)
            else:
                logger.info('Successfully installed dependencies!', extra=log_extra)

    def install(self, struct, ui, debug=False):
        """
        This is the only method that should be called from outside. Call it
        like:
        `DependencyInstaller(struct)` and it will install packages which are
        not present on system (it uses package managers specified by `struct`
        structure)
        """
        # the system dependencies should always go first
        self.__add_dependencies(self.get_system_deptype_shortcut(), [])
        for dep_dict in struct:
            for dep_t, dep_l in dep_dict.items():
                self._process_dependency(dep_t, dep_l)
        if self.dependencies:
            self._install_dependencies(ui, debug)

    def get_system_deptype_shortcut(self):
        local_distro = utils.get_distro_name()
        for dep_t, distros in settings.SYSTEM_DEPTYPES_SHORTCUTS.items():
            for distro in distros:
                if distro in local_distro:
                    return dep_t

        # just try rpm if unkown (not very nice?)
        return 'rpm'


class EndlessProgressThread(threading.Thread):
    def __init__(self, finish_event):
        super(EndlessProgressThread, self).__init__()
        self.finish_event = finish_event

    def run(self):
        log.info('Installing dependencies...')
        sleep = 1
        while not self.finish_event.isSet():
            log.info('...')
            time.sleep(int(math.log(sleep)))
            sleep += 2
