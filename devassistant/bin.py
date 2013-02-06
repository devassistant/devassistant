from devassistant import assistant_base
from devassistant import cli
from devassistant import yaml_loader

# for now, import Assistants by hand, but we may want to do this automatically
from devassistant.assistants import python

class MainAssistant(assistant_base.AssistantBase):
    def get_subassistants(self):
        sa = [python.PythonAssistant]
        sa.extend(yaml_loader.YamlLoader.get_top_level_assistants())
        return sa

    name = 'main'
    verbose_name = 'Main'

def main():
    cli.CliRunner.run_assistant(MainAssistant())
