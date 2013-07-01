import os

from devassistant import argument
from devassistant import yaml_loader
from devassistant import yaml_snippet_loader
from devassistant.assistants import yaml_assistant

class YamlAssistantLoader(object):
    assistants_dirs = [os.path.join(os.path.dirname(__file__), 'assistants', 'assistants')]
    _classes = []

    @classmethod
    def get_top_level_assistants(cls, roles=['creator', 'modifier', 'preparer']):
        assistants = cls.get_all_classes()
        are_subassistants = set()
        for a in assistants:
            if hasattr(a, '_subassistants'):
                are_subassistants.update(a._subassistants)
        top_level = filter(lambda x: x.name not in are_subassistants, assistants)
        return filter(lambda x: x.role in roles, top_level)

    @classmethod
    def get_all_classes(cls):
        if not cls._classes:
            parsed_yamls = yaml_loader.YamlLoader.load_all_yamls(cls.assistants_dirs)

            for s, y in parsed_yamls.items():
                cls._classes.append(cls.class_from_yaml(y))
                cls._classes[-1]._source_file = s

            for sa in cls._classes:
                if hasattr(sa, '_subassistants'):
                    # get subassistant classes of sa assistant
                    sub_classes = list(filter(lambda x: x.name in sa._subassistants, cls._classes))
                    sa.get_subassistants = cls.create_get_subassistants_method(sub_classes)

        return cls._classes

    @classmethod
    def create_get_subassistants_method(self, sa_list):
        def get_subassistants(self):
            return sa_list
        return get_subassistants

    @classmethod
    def class_from_yaml(cls, y):
        class CustomYamlAssistant(yaml_assistant.YamlAssistant): pass
        # assume only one key and value
        name, attrs = y.popitem()

        # arguments that we can handle right away
        CustomYamlAssistant.name = name
        CustomYamlAssistant.fullname = attrs.get('fullname', '')
        CustomYamlAssistant.description = attrs.get('description', '')
        CustomYamlAssistant.role = attrs.get('role', 'creator')
        # cli arguments
        CustomYamlAssistant.args = []
        yaml_args = attrs.get('args', {})
        for arg_name, arg_params in yaml_args.items():
            use_snippet = arg_params.pop('snippet', None)
            if use_snippet:
                # if snippet is used, take this parameter from snippet and update
                # it with current arg_params, if any
                snippet = yaml_snippet_loader.YamlSnippetLoader.get_snippet_by_name(use_snippet)
                # this works much like snippet.args.pop(arg_name).update(arg_params),
                # but unlike it, this actually returns the updated dict
                arg_params = dict(snippet.args.pop(arg_name, {}), **arg_params)

            arg = argument.Argument(*arg_params.pop('flags'), **arg_params)
            CustomYamlAssistant.args.append(arg)

        # arguments that will be handled by YamlAssistant methods
        CustomYamlAssistant._files = attrs.get('files', {})
        CustomYamlAssistant._subassistants = attrs.get('subassistants', [])
        CustomYamlAssistant._logging = attrs.get('logging', [])
        CustomYamlAssistant._dependencies = attrs.get('dependencies', [])
        # handle more dependencies* and run* sections
        for k, v in attrs.items():
            if k.startswith('run') or k.startswith('dependencies'):
                setattr(CustomYamlAssistant, '_{0}'.format(k), v)
        CustomYamlAssistant.pre_run = attrs.get('pre_run', [])
        CustomYamlAssistant.post_run = attrs.get('post_run', [])

        return CustomYamlAssistant
