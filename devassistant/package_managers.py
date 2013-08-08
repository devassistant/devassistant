# -*- coding: utf-8 -*-

"""
TODO:
 * merge prompts
  * issue only one prompt for dependencies
  * and one prompt for polkit
 * figure out how to install using pip when 'venv' option is specified
 * write tests
"""

from devassistant.command_helpers import RPMHelper, YUMHelper, PIPHelper, \
    DialogHelper

from devassistant.logger import logger
from devassistant import exceptions


def list_managers():
    """ return list of classes which represent package managers """
    def identify_managers(x):
        return x != PackageManager and isinstance(x, type) and \
            issubclass(x, PackageManager)
    # I admit that this is an absolutely insane hack but it's the simplest
    # solution and easy to maintain (no need to store list of package
    # managers somewhere)
    return filter(identify_managers, globals().values())


def list_managers_shortcuts():
    """ return list of shortcuts of package managers (e.g. ['rpm'])"""
    return map(lambda x: x.shortcut, list_managers())


class PackageManager(object):
    """ Abstract class for API definition of package managers """

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
        raise exceptions.CorePackagerMissing("yum can't be found, you are "
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


class PIPPackageManager(PackageManager):
    """ Package manager for managing python dependencies from PyPI """
    permission_prompt = "Install following %(packages_text)s from PyPI?"
    shortcut = 'pip'

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
        return PIPHelper.is_egg_installed(dep)

    @classmethod
    def resolve(cls, *dep):
        # depresolver for PyPI is infeasable to do -- there are no structured
        # metadata for python packages; so just return this dependency
        # PIPHelper.resolve(dep)
        return dep

    def __str__(self):
        return "pip package manager"


class DependencyInstaller(object):
    """ class for installing dependencies """
    def __init__(self):
        # {PackageManagerClass: ['list', 'of', 'dependencies']}
        self.dependencies = {}

    def get_package_manager(self, dep_t):
        """ choose proper package manager and return it """
        for glob in list_managers():
            if glob.match(dep_t):
                return glob
        logger.error(
            "Package manager for dependency type {0} was not found".
            format(dep_t))
        raise exceptions.PackageManagerNotFound(
            "Package manager for %s was not found." % dep_t)

    def _process_dependency(self, dep_t, dep_l):
        """ Add entry into self.dependencies """
        PackageManagerClass = self.get_package_manager(dep_t)
        self.dependencies.setdefault(PackageManagerClass, [])
        self.dependencies[PackageManagerClass].extend(dep_l)

    def _ask_to_confirm(self, pac_man, *to_install):
        """ Return True if user wants to install packages, False otherwise """
        message = '\n'.join(sorted(to_install))
        ret = DialogHelper.ask_for_confirm_with_message(
            prompt=pac_man.get_perm_prompt(len(to_install) > 1),
            message=message,
        )
        return False if ret is False else True

    def _check_dependencies(self, PackageManagerClass, deps):
        """ Check which deps are installed, return those who are not"""
        to_install = []
        for dep in deps:
            try:
                is_installed = PackageManagerClass.is_installed(dep)
            except exceptions.PackageManagerNotInstalled:
                # this package manager is not present on system, install it!
                di = DependencyInstaller()
                di.install([{'rpm': ['python-pip']}])
                is_installed = PackageManagerClass.is_installed(dep)
            if not is_installed:
                to_install.append(dep)
        return to_install

    def _install_dependencies(self):
        """ Install missing dependencies """
        for PackageManagerClass, deps in self.dependencies.iteritems():
            to_install = self._check_dependencies(PackageManagerClass, deps)
            if not to_install:
                # nothing to install, let's move on
                continue
            try:
                all_deps = PackageManagerClass.resolve(*to_install)
            except exceptions.CorePackagerMissing as e:
                logger.error(e.message)
                raise
            except Exception as e:
                logger.error('Failed to resolve dependencies: {exc}'.
                             format(exc=e))
                continue
            install = self._ask_to_confirm(PackageManagerClass, *all_deps)
            if install:
                installed = PackageManagerClass.install(*to_install)
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
