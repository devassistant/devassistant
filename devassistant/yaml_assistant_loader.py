import os

from devassistant import argument
from devassistant import exceptions
from devassistant.logger import logger
from devassistant import yaml_loader
from devassistant import yaml_snippet_loader
from devassistant import settings
from devassistant.assistants import yaml_assistant

class YamlAssistantLoader(object):
    assistants_dirs = list(map(lambda x: os.path.join(x, 'assistants'), settings.DATA_DIRECTORIES))
    # mapping of assistant load names (e.g. python/django) to assistant instances
    _assistants = {}

    @classmethod
    def get_top_level_assistants(cls, roles=['creator', 'modifier', 'preparer']):
        assistants = cls.get_all_assistants()
        are_subassistants = set()
        for a in assistants:
            are_subassistants.update(a._subassistant_names)
        top_level = filter(lambda x: x.name not in are_subassistants, assistants)
        return list(filter(lambda x: x.role in roles, top_level))

    @classmethod
    def get_all_assistants(cls):
        if not cls._assistants:
            parsed_yamls = yaml_loader.YamlLoader.load_all_yamls(cls.assistants_dirs)

            for s, y in parsed_yamls.items():
                new_as = cls.assistant_from_yaml(s, y)
                cls._assistants[new_as.name] = new_as

            # handle _superassistant_name fields
            have_super = filter(lambda a: a._superassistant_name is not None, cls._assistants.values())
            for assistant in have_super:
                cls._assistants[assistant._superassistant_name]._subassistant_names.append(assistant.name)

            for assistant in cls._assistants.values():
                # set subassistants of assistant according to names in _subassistant_names
                assistant._subassistants = [cls._assistants[n] for n in assistant._subassistant_names]

        return list(cls._assistants.values())

    @classmethod
    def assistant_from_yaml(cls, source, y):
        # assume only one key and value
        name, attrs = y.popitem()

        template_dir = attrs.get('template_dir', yaml_loader.YamlLoader._default_template_dir_for(source))
        assistant = yaml_assistant.YamlAssistant(name, attrs, source, template_dir)

        return assistant
