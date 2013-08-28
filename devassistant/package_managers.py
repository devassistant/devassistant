# -*- coding: utf-8 -*-

"""
TODO:
 * merge prompts
  * issue only one prompt for dependencies
  * and one prompt for polkit
 * figure out how to install using pip when 'venv' option is specified
 * write tests
"""
import collections
import logging
import platform
import tempfile

from devassistant.command_helpers import ClHelper, DialogHelper

from devassistant.logger import logger
from devassistant import exceptions

# list of shortcuts to managers
managers = {}

def register_manager(manager):
    managers[manager.shortcut] = manager
    return manager

class PackageManager(object):
    """ Abstract class for API definition of package managers """

    # Indicates whether this is a system manager. If so, dependencies of its type should be
    # skipped on platforms where it is not the default system manager.
    is_system = True

    @classmethod
    def match(cls, *args, **kwargs):
        """
        Return True if this package manager should be chosen as dep installer
        """
        raise NotImplementedError()

    @classmethod
    def get_perm_prompt(cls, *args, **kwargs):
        """
        Return text for prompt (do you want to install...), there should be
        argument `plural` indicating that only one package is being
        installed -- usable for text formatting
        """
        raise NotImplementedError()

    @classmethod
    def install(cls, *args, **kwargs):
        """Install dependency.

        Note: if you want your dependency installation to be uninterruptible, pass
        ignore_sigint=True to ClHelper.run_command.
        """
        raise NotImplementedError()

    @classmethod
    def is_installed(cls, *args, **kwargs):
        """Is this manager available?"""
        raise NotImplementedError()

    @classmethod
    def works(cls, *args, **kwargs):
        """Raises exceptions.PackageManagerNotOperational if this manager
        can't be used (something's missing) - e.g. for rpm manager
        is_installed() returns whether rpm is installed, but works() finds
        out whether the manager is usable."""
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


@register_manager
class RPMPackageManager(PackageManager):
    """ Package manager for managing rpm packages from repositories """
    permission_prompt = "Install following %(packages_text)s?"
    shortcut = 'rpm'

    c_rpm = 'rpm'
    c_yum = 'yum'

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
        logger.info('Checking for presence of {0}...'.format(rpm_name), extra={'event_type': 'dep_check'})

        found_rpm = cls.rpm_q(rpm_name)
        if found_rpm:
            logger.info('Found {0}'.format(found_rpm), extra={'event_type': 'dep_found'})
        else:
            logger.info('Not found, will install', extra={'event_type': 'dep_not_found'})
        return found_rpm

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
    def was_rpm_installed(cls, rpm_name):
        # TODO: handle failure
        found_rpm = cls.rpm_q(rpm_name)
        logger.info('Installed {0}'.format(found_rpm), extra={'event_type': 'dep_installed'})
        return found_rpm

    @classmethod
    def match(cls, dep_t):
        return dep_t == cls.shortcut

    @classmethod
    def get_perm_prompt(cls, plural=False):
        packages_text = 'packages' if plural else 'package'
        return cls.permission_prompt % {'packages_text': packages_text}

    @classmethod
    def install(cls, *args):
        cmd = ['pkexec', cls.c_yum, '-y', 'install']
        quoted_pkgs = map(lambda pkg: '"{pkg}"'.format(pkg=pkg), args)
        cmd.extend(quoted_pkgs)
        try:
            ClHelper.run_command(' '.join(cmd), log_level=logging.INFO, ignore_sigint=True)
            return args
        except exceptions.ClException:
            return False

    @classmethod
    def is_installed(cls, dep):
        try:
            ClHelper('which rpm')
            return True
        except exceptions.ClException:
            return False

    @classmethod
    def works(cls):
        try:
            import yum
            return True
        except ImportError:
            msg = 'Package manager for "{0}" not operational: {1}'.format(dep_t, e)
            logger.error(msg)
            raise exceptions.PackageManagerNotOperational(msg)

    @classmethod
    def is_pkg_installed(cls, pkg):
        return cls.is_group_installed(pkg) if pkg.startswith('@') else cls.is_rpm_installed(pkg)

    @classmethod
    def resolve(cls, *args):
        # TODO: we may need to rewrite this for e.g. suse, which
        # is rpm based, but doesn't use yum; same for install()/is_available()/can_operate()
        logger.info('Resolving dependencies ...')
        import yum
        y = yum.YumBase()
        y.setCacheDir(tempfile.mkdtemp())
        for pkg in args:
            if pkg.startswith('@'):
                y.selectGroup(pkg[1:])
            else:
                y.install(y.returnPackageByDep(pkg))
        y.resolveDeps()
        logger.debug('Installing/Updating:')
        to_install = []
        for pkg in y.tsInfo.getMembers():
            to_install.append(pkg.po.ui_envra)
            logger.debug(pkg.po.ui_envra)

        return to_install

    def __str__(self):
        return "rpm package manager"


@register_manager
class PIPPackageManager(PackageManager):
    """ Package manager for managing python dependencies from PyPI """
    permission_prompt = "Install following %(packages_text)s from PyPI?"
    shortcut = 'pip'
    is_system = False

    c_pip = 'pip'

    @classmethod
    def match(cls, dep_t):
        return dep_t == cls.shortcut

    @classmethod
    def get_perm_prompt(cls, plural=False):
        packages_text = 'packages' if plural else 'package'
        return cls.permission_prompt % {'packages_text': packages_text}

    @classmethod
    def install(cls, *args):
        cmd = [cls.c_pip, 'install', '--user']
        quoted_pkgs = map(lambda pkg: '"{pkg}"'.format(pkg=pkg), args)
        cmd.extend(quoted_pkgs)
        try:
            ClHelper.run_command(' '.join(cmd), log_level=logging.INFO, ignore_sigint=True)
            return args
        except exceptions.ClException:
            return False

    @classmethod
    def is_installed(cls):
        try:
            ClHelper.run_command('which pip')
            return True
        except exceptions.ClException:
            return False

    @classmethod
    def works(cls):
        try:
            ClHelper.run_command('pip')
            return True
        except exceptions.ClException as e:
            msg = 'Package manager for "{0}" not operational: {1}'.format(dep_t, e)
            logger.error(msg)
            raise exceptions.PackageManagerNotOperational(msg)

    @classmethod
    def is_pkg_installed(cls, dep):
        logger.info('Checking for presence of {0}...'.format(dep),
                    extra={'event_type': 'dep_check'})
        if not getattr(cls, '_installed', None):
            query = ClHelper.run_command(' '.join([cls.c_pip, 'list']))
            cls._installed = query.split('\n')
        search = filter(lambda e: e.startswith(dep + ' '), cls._installed)
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
        return dep

    @classmethod
    def get_distro_dependencies(self, smgr_sc):
        return ['python-pip']

    def __str__(self):
        return "pip package manager"


class DependencyInstaller(object):
    # True if devassistant is installing dependencies and we can't interrupt the process
    install_lock = False

    """Class for installing dependencies """
    def __init__(self):
        # {package_manager_shorcut: ['list', 'of', 'dependencies']}
        # we're using ordered dict to preserve the order that is used in
        # assistants; we also want system dependencies to always go first
        self.dependencies = collections.OrderedDict()

    def get_package_manager(self, dep_t):
        """Choose proper package manager and return it."""
        # one package manager can possibly handle multiple dep types,
        # so we can't just do manager.shortcut == dep_t
        for manager in managers.values():
            if manager.match(dep_t):
                return manager
        err = "Package manager for dependency type {0} was not found".format(dep_t)
        logger.error(err)
        raise exceptions.PackageManagerUnknown(err)

    def _process_dependency(self, dep_t, dep_l):
        """Add depednecnies into self.dependencies, possibly also adding system packages
        that contain non-distro package managers (e.g. if someone wants to install
        dependencines with pip and pip is not present, it will get installed through
        RPM on RPM based systems, etc.

        Skips dependencies that are supposed to be installed by system manager that
        is not native to this system.
        """
        if managers[dep_t].is_system and self.get_system_package_manager_shortcut() != dep_t:
            return
        if not managers[dep_t].is_system and not managers[dep_t].is_installed():
            smgr_sc = self.get_system_package_manager_shortcut()
            self._process_dependency(smgr_sc, managers[dep_t].get_distro_dependencies(smgr_sc))
        self.dependencies.setdefault(dep_t, [])
        self.dependencies[dep_t].extend(dep_l)

    def _ask_to_confirm(self, pac_man, *to_install):
        """ Return True if user wants to install packages, False otherwise """
        message = '\n'.join(sorted(to_install))
        ret = DialogHelper.ask_for_confirm_with_message(
            prompt=pac_man.get_perm_prompt(len(to_install) > 1),
            message=message,
        )
        return False if ret is False else True

    def _install_dependencies(self):
        """Install missing dependencies"""
        for dep_t, dep_l in self.dependencies.items():
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
            confirm = self._ask_to_confirm(pkg_mgr, *to_install)
            if not confirm:
                msg = 'List of packages denied by user, exiting.'
                logger.error(msg)
                raise exceptions.DependencyException(msg)

            type(self).install_lock = True
            installed = pkg_mgr.install(*to_install)
            type(self).install_lock = False

            if not installed:
                msg = 'Failed to install dependencies, exiting.'
                logger.error(msg)
                raise exceptions.DependencyException(msg)
            else:
                logger.info("Successfully installed {0}".format(', '.join(installed)))

    def install(self, struct):
        """
        This is the only method that should be called from outside. Call it
        like:
        `DependencyInstaller(struct)` and it will install packages which are
        not present on system (it uses package managers specified by `struct`
        structure)
        """
        # the system dependencies should always go first
        self.dependencies.setdefault(self.get_system_package_manager_shortcut(), [])
        for dep_dict in struct:
            for dep_t, dep_l in dep_dict.items():
                self._process_dependency(dep_t, dep_l)
        if self.dependencies:
            self._install_dependencies()

    def get_system_package_manager_shortcut(self):
        di = platform.linux_distribution()[0].lower()
        # TODO: rpm by default, custom logic for other distros

        return 'rpm'


def main():
    """ just for testing """
    import logging
    import sys
    from devassistant import logger as l
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(l.DevassistantClFormatter())
    console_handler.setLevel(logging.DEBUG)
    l.logger.addHandler(console_handler)

    di = DependencyInstaller()
    di.install([{'rpm': ['python-celery']}, {'pip': ['numpy', 'celery']}])

if __name__ == '__main__':
    main()
