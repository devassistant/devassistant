from devassistant import argument
from devassistant import assistant_base
from devassistant import chain_handler
from devassistant import path_runner
from devassistant import settings

# for now, import Assistants by hand, but we may want to do this automatically
from devassistant.assistants import python

class MainAssistant(assistant_base.AssistantBase):
    def get_subassistants(self):
        return [python.PythonAssistant]

    name = 'main'
    verbose_name = 'Main'

def main():
    ch = chain_handler.ChainHandler(MainAssistant.gather_subassistant_chain())
    parsed_args = ch.get_argument_parser().parse_args()
    path = ch.get_path_to(getattr(parsed_args, settings.SUBASSISTANTS_STRING))
    pr = path_runner.PathRunner(path, parsed_args)
    pr.run()
