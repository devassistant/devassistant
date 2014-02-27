import six

from devassistant import lang
from devassistant.logger import logger
from devassistant import exceptions
from devassistant import yaml_assistant


class PathRunner(object):
    def __init__(self, path, override_sys_excepthook=True):
        self.path = path
        if override_sys_excepthook:
            import devassistant.excepthook

    def _logging(self, parsed_args):
        """Registers a logging handler from the leaf assistant."""
        self.path[-1].logging(parsed_args)

    def _run_path_dependencies(self, parsed_args):
        """Installs dependencies from the leaf assistant.
        Raises:
            devassistant.exceptions.DependencyException with a cause if something goes wrong
        """
        deps = self.path[-1].dependencies(parsed_args)

        lang.Command('dependencies', deps, parsed_args).run()

    def _run_path_run(self, stage, parsed_args):
        """Runs run section with given stage from leaf assistants.
        Raises:
            devassistant.exceptions.RunException with a cause if something goes wrong
        """
        self.path[-1].run(stage, parsed_args)

    def run(self, **parsed_args):
        """Runs all errors, dependencies and run methods of all *Assistant objects in self.path.
        Raises:
            devassistant.exceptions.ExecutionException with a cause if something goes wrong
        """
        error = None
        # run 'pre_run', 'logging', 'dependencies' and 'run'
        try:  # serve as a central place for error logging
            self._logging(parsed_args)
            if not 'deps_only' in parsed_args:
                self._run_path_run('pre', parsed_args)
            self._run_path_dependencies(parsed_args)
            if not 'deps_only' in parsed_args:
                self._run_path_run('', parsed_args)
        except exceptions.ExecutionException as e:
            if not getattr(e, 'already_logged', False):
                # this is here primarily because of log_ command, that logs the message itself
                logger.error(six.text_type(e))
                if isinstance(e, exceptions.YamlError):  # if there's a yaml error, just shut down
                    raise e
            error = e

        # in any case, run post_run
        try:  # serve as a central place for error logging
            self._run_path_run('post', parsed_args)
        except exceptions.ExecutionException as e:
            if not getattr(e, 'already_logged', False):
                # this is here primarily because of log_ command, that logs the message itself
                logger.error(six.text_type(e))
            error = e

        if error:
            raise error

    def stop(self):
        for a in self.path:
            if 'run' in vars(a.__class__) or isinstance(a, yaml_assistant.YamlAssistant):
                a.stop()
