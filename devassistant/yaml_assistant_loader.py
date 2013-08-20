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
    # mapping of assistant roles to lists of top-level assistant instances
    _assistants = {}

    @classmethod
    def get_top_level_assistants(cls, roles=settings.ASSISTANT_ROLES):
        cls.load_all_assistants(roles=roles)
        result = []
        for r in roles:
            result.extend(cls._assistants[r])

        return result

    @classmethod
    def load_all_assistants(cls, roles):
        to_load = set(roles) - set(cls._assistants.keys())
        for tl in to_load:
            dirs = [os.path.join(d, tl) for d in cls.assistants_dirs]
            file_hierarchy = cls.get_assistants_file_hierarchy(dirs)
            cls._assistants[tl] = cls.get_assistants_from_file_hierarchy(file_hierarchy)

    @classmethod
    def get_assistants_from_file_hierarchy(cls, file_hierarchy):
        result = []

        for name, subhierarchy in file_hierarchy.items():
            loaded_yaml = yaml_loader.YamlLoader.load_yaml_by_path(subhierarchy[0])
            ass = cls.assistant_from_yaml(subhierarchy[0], loaded_yaml)
            ass._subassistants = cls.get_assistants_from_file_hierarchy(subhierarchy[1])
            result.append(ass)

        return result

    @classmethod
    def get_assistants_file_hierarchy(cls, dirs):
        result = {}
        for d in filter(lambda d: os.path.exists(d), dirs):
            for f in filter(lambda f: f.endswith('.yaml'), os.listdir(d)):
                assistant_name = f[:-5]
                if assistant_name not in result:
                    subas_dirs = [os.path.join(dr, assistant_name) for dr in dirs]
                    result[assistant_name] = (os.path.join(d, f),
                                              cls.get_assistants_file_hierarchy(subas_dirs))

        return result

    @classmethod
    def assistant_from_yaml(cls, source, y):
        # assume only one key and value
        name, attrs = y.popitem()

        template_dir = attrs.get('template_dir', yaml_loader.YamlLoader._default_template_dir_for(source))
        assistant = yaml_assistant.YamlAssistant(name, attrs, source, template_dir)

        return assistant
