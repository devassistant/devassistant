from devassistant import argument
from devassistant import assistant_base

class PythonAssistant(assistant_base.AssistantBase):
    name = 'python'
    verbose_name = 'Python'

    args = []
    usage_string_fmt = 'Usage of {verbose_name}:'

class DjangoAssistant(assistant_base.PythonAssistant):
    name = 'django'
    verbose_name = 'Django'

    args = [argument.Argument('-n', '--name')]
    usage_string_fmt = 'Usage of {verbose_name}:'
