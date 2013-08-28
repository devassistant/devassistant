from devassistant import argument
from devassistant import assistant_base
from devassistant import cli
from devassistant import settings
from devassistant import yaml_assistant_loader

class ExecutableAssistant(assistant_base.AssistantBase):
    args = [argument.Argument('deps_only',
                              settings.DEPS_ONLY_FLAG,
                              help='Only install dependencies',
                              required=False,
                              action='store_true')]

    @classmethod
    def main(cls):
        cli.CliRunner.run_assistant(cls())

class CreatorAssistant(ExecutableAssistant):
    def get_subassistants(self):
        sa = yaml_assistant_loader.YamlAssistantLoader.get_top_level_assistants(roles=['creator'])
        return sa

    name = 'main'
    verbose_name = 'Main'
    description = 'Kickstart new projects easily with devassistant.'

class ModifierAssistant(ExecutableAssistant):
    def get_subassistants(self):
        sa = yaml_assistant_loader.YamlAssistantLoader.get_top_level_assistants(roles=['modifier'])
        return sa

    name = 'main'
    verbose_name = 'Main'
    description = 'Modify existing projects with devassistant.'

class PreparerAssistant(ExecutableAssistant):
    def get_subassistants(self):
        sa = yaml_assistant_loader.YamlAssistantLoader.get_top_level_assistants(roles=['preparer'])
        return sa

    name = 'main'
    verbose_name = 'Main'
    description = 'Prepare environment for upstream projects or various tasks with devassistant.'
