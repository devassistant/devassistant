from devassistant import argument
from devassistant import assistant_base
from devassistant import chain_handler
from devassistant import settings

# for now, import Assistants by hand, but we may want to do this automatically
from devassistant.assistants import python

class MainAssistant(assistant_base.AssistantBase):
    def get_subassistants(self):
        return [python.PythonAssistant]

    name = 'main'
    verbose_name = 'Main'

    usage_string_fmt = 'Usage of {verbose_name}'

def main():
    ch = chain_handler.ChainHandler(MainAssistant.gather_subassistant_chain())
    print ch.chain
    parsed_args = ch.get_argument_parser().parse_args()
    print parsed_args
