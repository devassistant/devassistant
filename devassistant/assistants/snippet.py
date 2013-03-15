import os

class Snippet(object):
    def __init__(self, path, parsed_yaml):
        self.path = path
        self.name = os.path.splitext(os.path.basename(path))[0]
        self.parsed_yaml = parsed_yaml

    @property
    def args(self):
        return self.parsed_yaml.get('args', {})

    def get_arg_by_name(self, name):
        return self.args.get(name, {})

    @property
    def run_section(self):
        print self.parsed_yaml
        return self.parsed_yaml.get('run', {})
