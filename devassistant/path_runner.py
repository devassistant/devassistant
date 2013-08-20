from devassistant import exceptions
from devassistant.assistants import yaml_assistant
from devassistant.assistants.commands import run_command

class PathRunner(object):
    def __init__(self, path, parsed_args, override_sys_excepthook=True):
        self.path = path
        self.parsed_args = parsed_args
        self.stop_flag = False
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

    def _run_path_dependencies(self):
        """Runs *Assistant.dependencies methods.
        Raises:
            devassistant.exceptions.DependencyException with a cause if something goes wrong
        """
        deps = []

        for a in self.path:
            if 'dependencies' in vars(a.__class__) or isinstance(a, yaml_assistant.YamlAssistant):
                deps.extend(a.dependencies(**self.parsed_args))

        run_command('dependencies', deps)

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
        if not 'deps_only' in self.parsed_args:
            self._run_path_run()
            
    def stop_assistant(self):
        self.stop_flag = True
        for a in self.path:
            if 'run' in vars(a.__class__) or isinstance(a, yaml_assistant.YamlAssistant):
                """
                Setting stop_flag into YamlAssistant
                """
                a.stop_action(self.stop_flag)
        
