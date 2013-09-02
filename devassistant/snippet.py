import copy

class Snippet(object):
    def __init__(self, name, parsed_yaml, path, template_dir=''):
        self.name = name
        self.parsed_yaml = parsed_yaml
        self.path = path
        self.template_dir = template_dir

    @property
    def args(self):
        return copy.deepcopy(self.parsed_yaml.get('args', {}))

    def get_arg_by_name(self, name):
        return self.args.get(name, {})

    def get_run_section(self, section_name='run'):
        return copy.deepcopy(self.parsed_yaml.get(section_name, None))

    def get_template_dir(self):
        return self.parsed_yaml.get('template_dir', self.template_dir)

    def get_dependencies_section(self, section_name='dependencies'):
        if not section_name in self.parsed_yaml:
            return None
        # we also want to include the basic "dependencies" section
        deps = copy.deepcopy(self.parsed_yaml.get('dependencies', []))
        if section_name != 'dependencies':
            deps.extend(copy.deepcopy(self.parsed_yaml.get(section_name, [])))
        return deps

    def get_files_section(self):
        return copy.deepcopy(self.parsed_yaml.get('files', {}))
