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

    def get_all_names(self):
        return [self.name] + self.aliases


class CreatorAssistant(ExecutableAssistant):
    def get_subassistants(self):
        sa = yaml_assistant_loader.YamlAssistantLoader.get_assistants(superassistants=[self])
        return sa

    name = 'crt'
    aliases = ['create']
    fullname = 'Create Project'
    description = 'Kickstart new projects easily with DevAssistant.'


class TweakAssistant(ExecutableAssistant):
    def get_subassistants(self):
        sa = yaml_assistant_loader.YamlAssistantLoader.get_assistants(superassistants=[self])
        return sa

    name = 'twk'
    # TODO: in 1.0.0, remove mod and modify
    aliases = ['tweak', 'mod', 'modify']
    fullname = 'Tweak Existing Project'
    description = 'Tweak existing projects with DevAssistant.'


class PreparerAssistant(ExecutableAssistant):
    def get_subassistants(self):
        sa = yaml_assistant_loader.YamlAssistantLoader.get_assistants(superassistants=[self])
        return sa

    name = 'prep'
    aliases = ['prepare']
    fullname = 'Prepare Environment'
    description = 'Prepare environment for upstream projects with DevAssistant.'


class ExtrasAssistant(ExecutableAssistant):
    def get_subassistants(self):
        sa = yaml_assistant_loader.YamlAssistantLoader.get_assistants(superassistants=[self])
        return sa

    name = 'extra'
    # TODO: in 1.0.0, remove task
    aliases = ['extras', 'task']
    fullname = 'Extras'
    description = 'Perform a custom task not related to a specific project.'


class TopAssistant(assistant_base.AssistantBase):
    _assistants = []

    def get_subassistants(self):
        # cache assistants to always return the same instances
        if not self._assistants:
            self._assistants = [CreatorAssistant(), TweakAssistant(),
                                PreparerAssistant(), ExtrasAssistant()]
        return self._assistants
