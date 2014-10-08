import copy

from devassistant import loaded_yaml


class Snippet(loaded_yaml.LoadedYaml):
    def __init__(self, dotted_name, parsed_yaml, path):
        self.name = dotted_name.split('.')[-1]
        self.dotted_name = dotted_name
        self.parsed_yaml = parsed_yaml
        self.path = path

    @property
    def args(self):
        return copy.deepcopy(self.parsed_yaml.get('args') or {})

    def get_arg_by_name(self, name):
        return self.args.get(name) or {}

    def get_run_section(self, section_name='run'):
        return copy.deepcopy(self.parsed_yaml.get(section_name))

    def get_files_dir(self):
        return self.parsed_yaml.get('files_dir') or self.default_files_dir_for('snippets')

    def get_dependencies_section(self, section_name='dependencies'):
        if section_name not in self.parsed_yaml:
            return None
        # we also want to include the basic "dependencies" section
        deps = copy.deepcopy(self.parsed_yaml.get('dependencies', []))
        if section_name != 'dependencies':
            deps.extend(copy.deepcopy(self.parsed_yaml.get(section_name, [])))
        return deps

    def get_files_section(self):
        return copy.deepcopy(self.parsed_yaml.get('files') or {})
