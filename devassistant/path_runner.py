from devassistant import lang
from devassistant.logger import logger
from devassistant import exceptions
from devassistant import utils
from devassistant import yaml_assistant


class PathRunner(object):
    def __init__(self, path, args, override_sys_excepthook=True):
        self.path = path
        self.parsed_args = args
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

    def _log_if_not_logged(self, err):
        if not getattr(err, 'already_logged', False):
            # this is here primarily because of log_ command, that logs the message itself
            logger.error(utils.exc_as_decoded_string(err))

        return err

    def run(self):
        """Runs all errors, dependencies and run methods of all *Assistant objects in self.path.
        Raises:
            devassistant.exceptions.ExecutionException with a cause if something goes wrong
        """
        error = None
        # run 'pre_run', 'logging', 'dependencies' and 'run'
        try:  # serve as a central place for error logging
            self._logging(self.parsed_args)
            if 'deps_only' not in self.parsed_args:
                self._run_path_run('pre', self.parsed_args)
            self._run_path_dependencies(self.parsed_args)
            if 'deps_only' not in self.parsed_args:
                self._run_path_run('', self.parsed_args)
        except exceptions.ExecutionException as e:
            error = self._log_if_not_logged(e)
            if isinstance(e, exceptions.YamlError):  # if there's a yaml error, just shut down
                raise e

        # in any case, run post_run
        try:  # serve as a central place for error logging
            self._run_path_run('post', self.parsed_args)
        except exceptions.ExecutionException as e:
            error = self._log_if_not_logged(e)

        # exitfuncs are run all regardless of exceptions; if there is an exception in one
        #  of them, this function will raise it at the end
        try:
            utils.run_exitfuncs()
        except exceptions.ExecutionException as e:
            error = self._log_if_not_logged(e)

        if error:
            raise error

    def stop(self):
        for a in self.path:
            if 'run' in vars(a.__class__) or isinstance(a, yaml_assistant.YamlAssistant):
                a.stop()
