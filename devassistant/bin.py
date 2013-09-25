from devassistant import argument
from devassistant import assistant_base
from devassistant import settings
from devassistant import yaml_assistant_loader

class ExecutableAssistant(assistant_base.AssistantBase):
    args = [argument.Argument('deps_only',
                              settings.DEPS_ONLY_FLAG,
                              help='Only install dependencies',
                              required=False,
                              action='store_true')]

class CreatorAssistant(ExecutableAssistant):
    def get_subassistants(self):
        sa = yaml_assistant_loader.YamlAssistantLoader.get_top_level_assistants(roles=['creator'])
        return sa

    name = 'crt'
    fullname = 'Create Projects'
    description = 'Kickstart new projects easily with DevAssistant.'

class ModifierAssistant(ExecutableAssistant):
    def get_subassistants(self):
        sa = yaml_assistant_loader.YamlAssistantLoader.get_top_level_assistants(roles=['modifier'])
        return sa

    name = 'mod'
    fullname = 'Modify Projects'
    description = 'Modify existing projects with DevAssistant.'

class PreparerAssistant(ExecutableAssistant):
    def get_subassistants(self):
        sa = yaml_assistant_loader.YamlAssistantLoader.get_top_level_assistants(roles=['preparer'])
        return sa

    name = 'prep'
    fullname = 'Prepare Environment'
    description = 'Prepare environment for upstream projects or various tasks with DevAssistant.'

class TopAssistant(assistant_base.AssistantBase):
    def get_subassistants(self):
        return [CreatorAssistant(), ModifierAssistant(), PreparerAssistant()]
