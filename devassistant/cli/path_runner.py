from devassistant import exceptions
from devassistant.logger import logger

class PathRunner(object):
    def __init__(self, path, parsed_args):
        self.path = path
        self.parsed_args = parsed_args

    def _run_path_errors(self):
        """Gathers errors from *Assistant.errors methods
        Returns:
            List of found errors (empty list if everything is ok).
        """
        errors = []
        for a in self.path:
            if 'errors' in vars(a.__class__):
                errors.extend(a.errors(**vars(self.parsed_args)))
        return errors

    def _run_path_prepare(self):
        """Runs *Assistant.prepare methods.
        Raises:
            devassistant.exceptions.PrepareException with a cause if something goes wrong
        """
        for a in self.path:
            if 'prepare' in vars(a.__class__):
                a.prepare(**vars(self.parsed_args))

    def _run_path_run(self):
        """Runs *Assistant.run methods.
        Raises:
            devassistant.exceptions.RunException with a cause if something goes wrong
        """
        for a in self.path:
            if 'run' in vars(a.__class__):
                a.run(**vars(self.parsed_args))

    def run(self):
        """Runs all errors, prepare and run methods of all *Assistant objects in self.path.
        Raises:
            devassistant.exceptions.ExecutionException with a cause if something goes wrong
        """
        errors = self._run_path_errors()
        if errors:
            raise exceptions.ExecutionException(errors)
        self._run_path_prepare()
        self._run_path_run()
