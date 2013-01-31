from devassistant import assistant_base
from devassistant import cli

# for now, import Assistants by hand, but we may want to do this automatically
from devassistant.assistants import python

class MainAssistant(assistant_base.AssistantBase):
    def get_subassistants(self):
        return [python.PythonAssistant]

    name = 'main'
    verbose_name = 'Main'

def main():
    cli.CliRunner.run_assistant(MainAssistant)
