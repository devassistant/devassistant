from devassistant import argument
from devassistant import assistant_base
from devassistant import settings

class PythonAssistant(assistant_base.AssistantBase):
    def get_subassistants(self):
        return [DjangoAssistant]

    name = 'python'
    verbose_name = 'Python'

    usage_string_fmt = 'Usage of {verbose_name}:'

class DjangoAssistant(PythonAssistant):
    def __init__(self):
        pass

    name = 'django'
    verbose_name = 'Django'

    args = [argument.Argument('-n', '--name')]
    usage_string_fmt = 'Usage of {verbose_name}:'
