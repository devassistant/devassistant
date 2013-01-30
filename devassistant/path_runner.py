class PathRunner(object):
    def __init__(self, path, parsed_args):
        self.path = path
        self.parsed_args = parsed_args

    def _run_path_errors(self):
        for a in self.path:
            if 'errors' in vars(a.__class__):
                a.errors(**vars(self.parsed_args))

    def _run_path_prepare(self):
        for a in self.path:
            if 'prepare' in vars(a.__class__):
                a.prepare(**vars(self.parsed_args))

    def _run_path_run(self):
        for a in self.path:
            if 'run' in vars(a.__class__):
                a.run(**vars(self.parsed_args))

    def run(self):
        self._run_path_errors()
        self._run_path_prepare()
        self._run_path_run()
