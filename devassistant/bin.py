from devassistant import assistant_base
from devassistant import cli
from devassistant import yaml_assistant_loader

class MainAssistant(assistant_base.AssistantBase):
    def get_subassistants(self):
        sa = yaml_assistant_loader.YamlAssistantLoader.get_top_level_assistants()
        return sa

    name = 'main'
    verbose_name = 'Main'
    description = 'Developer assistant will help you with creating projects in many different languages.\
                   See subassistants for list of currently available assistants.'

def main():
    cli.CliRunner.run_assistant(MainAssistant())
