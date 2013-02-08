import os
import yaml

from devassistant import argument
from devassistant.assistants import yaml_assistant

class YamlLoader(object):
    yaml_dir = os.path.join(os.path.dirname(__file__), 'assistants', 'yaml')

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
        parsed_yamls = []
        for f in os.listdir(cls.yaml_dir):
            if f.endswith('.yaml'):
                with open(os.path.join(cls.yaml_dir, f), 'r') as stream:
                    parsed_yamls.append(yaml.load(stream))
        classes = []
        for y in parsed_yamls:
            classes.append(cls.class_from_yaml(y))

        for sa in classes:
            if hasattr(sa, '_subassistants'):
                # get subassistant classes of sa assistant
                sub_classes = filter(lambda x: x.name in sa._subassistants, classes)
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
        # cli arguments
        CustomYamlAssistant.args = []
        yaml_args = attrs.get('args', {})
        for arg_name, arg_params in yaml_args.items():
            arg = argument.Argument(*arg_params.pop('flags'), **arg_params)
            CustomYamlAssistant.args.append(arg)

        # arguments that will be handled by YamlAssistant methods
        CustomYamlAssistant._dependencies = attrs.get('dependencies', {})
        CustomYamlAssistant._fail_if = attrs.get('fail_if', [])
        CustomYamlAssistant._files = attrs.get('files', {})
        CustomYamlAssistant._subassistants = attrs.get('subassistants', [])
        # handle more run* sections
        for k, v in attrs.items():
            if k.startswith('run'):
                setattr(CustomYamlAssistant, '_{0}'.format(k), v)

        return CustomYamlAssistant
