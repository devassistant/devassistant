import copy
import os

class Snippet(object):
    def __init__(self, path, parsed_yaml):
        self.path = path
        self.name = os.path.splitext(os.path.basename(path))[0]
        self.parsed_yaml = parsed_yaml

    @property
    def args(self):
        return copy.deepcopy(self.parsed_yaml.get('args', {}))

    def get_arg_by_name(self, name):
        return self.args.get(name, {})

    def get_run_section(self, section_name='run'):
        return copy.deepcopy(self.parsed_yaml.get(section_name or 'run', {}))
