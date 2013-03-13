import os

class Snippet(object):
    def __init__(self, path, run_section):
        self.path = path
        self.name = os.path.splitext(os.path.basename(path))[0]
        self.run_section = run_section
