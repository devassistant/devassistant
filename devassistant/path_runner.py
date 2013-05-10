import sys

from devassistant import exceptions
from devassistant.assistants import yaml_assistant
from devassistant.command_helpers import RPMHelper, YUMHelper

class PathRunner(object):
    def __init__(self, path, parsed_args, override_sys_excepthook=True):
        self.path = path
        self.parsed_args = parsed_args
        if override_sys_excepthook:
            import devassistant.excepthook

    def _logging(self):
        """Registers a logging handler from the leaf assistant, if specified"""
        if 'logging' in vars(self.path[-1].__class__) or isinstance(self.path[-1], yaml_assistant.YamlAssistant):
            self.path[-1].logging(**self.parsed_args)

    def _run_path_errors(self):
        """Gathers errors from *Assistant.errors methods
        Returns:
            List of found errors (empty list if everything is ok).
        """
        errors = []
        for a in self.path:
            if 'errors' in vars(a.__class__) or isinstance(a, yaml_assistant.YamlAssistant):
                errors.extend(a.errors(**self.parsed_args))
        return errors

    def _install_rpm_dependencies(self, *dep_list, **kwargs):
        to_install = []

        for dep in dep_list:
            if dep.startswith('@'):
                if not YUMHelper.is_group_installed(dep):
                    to_install.append(dep)
            else:
                if not RPMHelper.is_rpm_installed(dep):
                    to_install.append(dep)

        if to_install: # only invoke YUM if we actually have something to install
            if not YUMHelper.install(*to_install):
                raise exceptions.RunException('Failed to install: {0}'.format(' '.join(to_install)))

        for pkg in to_install:
            RPMHelper.was_rpm_installed(pkg)

    def _run_path_dependencies(self):
        """Runs *Assistant.dependencies methods.
        Raises:
            devassistant.exceptions.DependencyException with a cause if something goes wrong
        """
        deps = []

        for a in self.path:
            if 'dependencies' in vars(a.__class__) or isinstance(a, yaml_assistant.YamlAssistant):
                deps.extend(a.dependencies(**self.parsed_args))

        # collide rpm deps to install them in one shot, install them first
        rpm_deps = reduce(lambda x, y: x + y, [dep[1] for dep in deps if dep[0] == 'rpm'], [])
        other_deps = [dep for dep in deps if dep[0] != 'rpm']

        self._install_rpm_dependencies(*rpm_deps, **self.parsed_args)

    def _run_path_run(self):
        """Runs *Assistant.run methods.
        Raises:
            devassistant.exceptions.RunException with a cause if something goes wrong
        """
        for a in self.path:
            if 'run' in vars(a.__class__) or isinstance(a, yaml_assistant.YamlAssistant):
                a.run(**self.parsed_args)

    def run(self):
        """Runs all errors, dependencies and run methods of all *Assistant objects in self.path.
        Raises:
            devassistant.exceptions.ExecutionException with a cause if something goes wrong
        """
        self._logging()
        errors = self._run_path_errors()
        if errors:
            raise exceptions.ExecutionException(errors)
        self._run_path_dependencies()
        self._run_path_run()
