import os
import yaml

from devassistant import argument
from devassistant import yaml_loader
from devassistant.assistants import yaml_assistant

class YamlAssistantLoader(object):
    assistants_dirs = [os.path.join(os.path.dirname(__file__)), 'assistants', 'yaml']

    @classmethod
    def get_top_level_assistants(cls):
        assistants = cls.get_all_classes()
        are_subassistants = set()
        for a in assistants:
            if hasattr(a, '_subassistants'):
                are_subassistants.update(a._subassistants)
        return filter(lambda x: x.name not in are_subassistants, assistants)

    @classmethod
    def get_all_classes(cls):
        parsed_yamls = yaml_loader.YamlLoader.load_all_yamls(cls.assistants_dirs)
        classes = []

        for y in parsed_yamls.values():
            classes.append(cls.class_from_yaml(y))

        for sa in classes:
            if hasattr(sa, '_subassistants'):
                # get subassistant classes of sa assistant
                sub_classes = list(filter(lambda x: x.name in sa._subassistants, classes))
                sa.get_subassistants = cls.create_get_subassistants_method(sub_classes)

        return classes

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
        # cli arguments
        CustomYamlAssistant.args = []
        yaml_args = attrs.get('args', {})
        for arg_name, arg_params in yaml_args.items():
            arg = argument.Argument(*arg_params.pop('flags'), **arg_params)
            CustomYamlAssistant.args.append(arg)

        # arguments that will be handled by YamlAssistant methods
        CustomYamlAssistant._dependencies = attrs.get('dependencies', [])
        CustomYamlAssistant._files = attrs.get('files', {})
        CustomYamlAssistant._subassistants = attrs.get('subassistants', [])
        CustomYamlAssistant._logging = attrs.get('logging', [])
        # handle more run* sections
        for k, v in attrs.items():
            if k.startswith('run'):
                setattr(CustomYamlAssistant, '_{0}'.format(k), v)

        return CustomYamlAssistant
