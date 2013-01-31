from devassistant.logger import logger

class PathRunner(object):
    def __init__(self, path, parsed_args):
        self.path = path
        self.parsed_args = parsed_args

    def _run_path_errors(self):
        errors = []
        for a in self.path:
            if 'errors' in vars(a.__class__):
                errors.extend(a.errors(**vars(self.parsed_args)))
        return errors

    def _run_path_prepare(self):
        for a in self.path:
            if 'prepare' in vars(a.__class__):
                a.prepare(**vars(self.parsed_args))

    def _run_path_run(self):
        for a in self.path:
            if 'run' in vars(a.__class__):
                a.run(**vars(self.parsed_args))

    def run(self):
        errors = self._run_path_errors()
        if errors:
            logger.error('Can\'t continue because of errors, aborting.')
            return
        self._run_path_prepare()
        self._run_path_run()
