from devassistant import argument
from devassistant import assistant_base
from devassistant import settings
from devassistant import yaml_assistant_loader


class ExecutableAssistant(assistant_base.AssistantBase):
    aliases = []
    args = [argument.Argument('deps_only',
                              settings.DEPS_ONLY_FLAG,
                              help='Only install dependencies',
                              required=False,
                              action='store_true')]


class CreatorAssistant(ExecutableAssistant):
    def get_subassistants(self):
        sa = yaml_assistant_loader.YamlAssistantLoader.get_assistants(superassistants=[self])
        return sa

    name = 'crt'
    aliases = ['create']
    fullname = 'Create Project'
    description = 'Kickstart new projects easily with DevAssistant.'


class ModifierAssistant(ExecutableAssistant):
    def get_subassistants(self):
        sa = yaml_assistant_loader.YamlAssistantLoader.get_assistants(superassistants=[self])
        return sa

    name = 'mod'
    aliases = ['modify']
    fullname = 'Modify Project'
    description = 'Modify existing projects with DevAssistant.'


class PreparerAssistant(ExecutableAssistant):
    def get_subassistants(self):
        sa = yaml_assistant_loader.YamlAssistantLoader.get_assistants(superassistants=[self])
        return sa

    name = 'prep'
    aliases = ['prepare']
    fullname = 'Prepare Environment'
    description = 'Prepare environment for upstream projects with DevAssistant.'


class TaskAssistant(ExecutableAssistant):
    def get_subassistants(self):
        sa = yaml_assistant_loader.YamlAssistantLoader.get_assistants(superassistants=[self])
        return sa

    name = 'task'
    fullname = 'Custom Task'
    description = 'Perform a custom task not related to a specific project with DevAssistant.'


class TopAssistant(assistant_base.AssistantBase):
    _assistants = []

    def get_subassistants(self):
        # cache assistants to always return the same instances
        if not self._assistants:
            self._assistants = [CreatorAssistant(), ModifierAssistant(),
                                PreparerAssistant(), TaskAssistant()]
        return self._assistants
