# -*- coding: utf-8 -*-

"""
TODO:
 * merge prompts
  * issue only one prompt for dependencies
  * and one prompt for polkit
 * figure out how to install using pip when 'venv' option is specified
 * write tests
"""
import platform

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
        """ Install dependency """
        raise NotImplementedError()

    @classmethod
    def install_package_manager(cls, *args, **kwargs):
        """ Install actual package manager """
        raise NotImplementedError()

    @classmethod
    def is_installed(cls, *args, **kwargs):
        """ Is dependency already installed? """
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

    @classmethod
    def match(cls, dep_t):
        return dep_t == cls.shortcut

    @classmethod
    def get_perm_prompt(cls, plural=False):
        packages_text = 'packages' if plural else 'package'
        return cls.permission_prompt % {'packages_text': packages_text}

    @classmethod
    def install(cls, *args):
        return YUMHelper.install(*args)

    @classmethod
    def install_package_manager(cls):
        # yum is missing, user has to fix it
        raise exceptions.SystemPackageManagerMissing("yum can't be found, you are "
            "probably running developer assistant in sandbox (virtualenv).")

    @classmethod
    def is_installed(cls, dep):
        if dep.startswith('@'):
            return YUMHelper.is_group_installed(dep)
        else:
            return RPMHelper.is_rpm_installed(dep)

    @classmethod
    def resolve(cls, *args):
        return YUMHelper.resolve(*args)

    def __str__(self):
        return "rpm package manager"


@register_manager
class PIPPackageManager(PackageManager):
    """ Package manager for managing python dependencies from PyPI """
    permission_prompt = "Install following %(packages_text)s from PyPI?"
    shortcut = 'pip'
    is_system = False

    @classmethod
    def match(cls, dep_t):
        return dep_t == cls.shortcut

    @classmethod
    def get_perm_prompt(cls, plural=False):
        packages_text = 'packages' if plural else 'package'
        return cls.permission_prompt % {'packages_text': packages_text}

    @classmethod
    def install(cls, *dep):
        """ Install dependency """
        return PIPHelper.install(*dep)

    @classmethod
    def install_package_manager(cls):
        # pip is missing, install it
        logger.warn("pip is missing")
        di = DependencyInstaller()
        di.install([{'rpm': ['python-pip']}])

    @classmethod
    def is_installed(cls, dep):
        try:
            ClHelper('which pip')
            return True
        except exceptions.ClException:
            return False

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
    """Class for installing dependencies """
    def __init__(self):
        # {PackageManagerClass: ['list', 'of', 'dependencies']}
        self.dependencies = {}

    def get_package_manager(self, dep_t):
        """Choose proper package manager and return it."""
        # one package manager can possibly handle multiple dep types,
        # so we can't just do manager.shortcut == dep_t
        for manager in managers.values():
            if manager.match(dep_t):
                return manager
        err = "Package manager for dependency type {0} was not found".format(dep_t)
        logger.error(err)
        raise exceptions.PackageManagerNotFound(err)

    def _process_dependency(self, dep_t, dep_l):
        """Add depednecnies into self.dependencies, possibly also adding system packages
        that contain non-distro package managers (e.g. if someone wants to install
        dependencines with pip and pip is not present, it will get installed through
        RPM on RPM based systems, etc."""
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
        """ Install missing dependencies """
        for dep_t, dep_l in self.dependencies.items():
            pkg_mgr = self.get_package_manager(dep_t)
            to_install = pkg_mgr.resolve(*dep_l)
            if not to_install:
                # nothing to install, let's move on
                continue
            except Exception as e:
                logger.error('Failed to resolve dependencies: {exc}'.
                             format(exc=e))
                continue
            install = self._ask_to_confirm(pkg_mgr, *all_deps)
            if install:
                installed = pkg_mgr.install(*to_install)
                logger.info("Successfully installed {0}".format(installed))

    def install(self, struct):
        """
        This is the only method that should be called from outside. Call it
        like:
        `DependencyInstaller(struct)` and it will install packages which are
        not present on system (it uses package managers specified by `struct`
        structure)
        """
        for dep_dict in struct:
            for dep_t, dep_l in dep_dict.items():
                self._process_dependency(dep_t, dep_l)
        if self.dependencies:
            self._install_dependencies()

    def get_system_package_manager_shortcut(self):
        di = platform.linux_distribution[0].lower()
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
