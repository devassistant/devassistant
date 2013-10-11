from devassistant import yaml_assistant
from devassistant import command

class PathRunner(object):
    def __init__(self, path, override_sys_excepthook=True):
        self.path = path
        if override_sys_excepthook:
            import devassistant.excepthook

    def _logging(self, **parsed_args):
        """Registers a logging handler from the leaf assistant, if specified"""
        if 'logging' in vars(self.path[-1].__class__) or isinstance(self.path[-1], yaml_assistant.YamlAssistant):
            self.path[-1].logging(**parsed_args)

    def _run_path_dependencies(self, **parsed_args):
        """Runs *Assistant.dependencies methods.
        Raises:
            devassistant.exceptions.DependencyException with a cause if something goes wrong
        """
        deps = []

        for a in self.path:
            if 'dependencies' in vars(a.__class__) or isinstance(a, yaml_assistant.YamlAssistant):
                deps.extend(a.dependencies(**parsed_args))

        command.Command('dependencies',
                        deps,
                        self.path[-1].proper_kwargs(section='dependencies', **parsed_args)).run()

    def _run_path_run(self, **parsed_args):
        """Runs *Assistant.run methods.
        Raises:
            devassistant.exceptions.RunException with a cause if something goes wrong
        """
        for a in self.path:
            if 'run' in vars(a.__class__) or isinstance(a, yaml_assistant.YamlAssistant):
                a.run(**parsed_args)

    def run(self, **parsed_args):
        """Runs all errors, dependencies and run methods of all *Assistant objects in self.path.
        Raises:
            devassistant.exceptions.ExecutionException with a cause if something goes wrong
        """
        self._logging(**parsed_args)
        self._run_path_dependencies(**parsed_args)
        if not 'deps_only' in parsed_args:
            self._run_path_run(**parsed_args)

    def stop(self):
        for a in self.path:
            if 'run' in vars(a.__class__) or isinstance(a, yaml_assistant.YamlAssistant):
                a.stop()
