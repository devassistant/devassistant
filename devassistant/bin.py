from devassistant import argument
from devassistant import assistant_base
from devassistant import settings

# for now, import Assistants by hand, but we may want to do this automatically
from devassistant.assistants import python

class MainAssistant(assistant_base.AssistantBase):
    name = 'main'
    verbose_name = 'Main'

    usage_string_fmt = 'Usage of {verbose_name}'

    args = [argument.Argument(settings.SUBASSISTANTS_STRING,
                              subassistants={python.PythonAssistant.name: python.PythonAssistant})]

def main():
    parsed_args = MainAssistant().get_argument_parser().parse_args()
