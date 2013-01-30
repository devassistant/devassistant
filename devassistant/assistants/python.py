from devassistant import argument
from devassistant import assistant_base
from devassistant import settings

from devassistant.command_helpers import RPMHelper, YUMHelper

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

    def prepare(self, **kwargs):
        self.install_django = False
        if not RPMHelper.is_rpm_present('python-django'):
            self.install_django = True
            self.needs_sudo = True

    def run(self, **kwargs):
        if self.install_django:
            YUMHelper.install('python-django')

    args = [argument.Argument('-n', '--name')]
    usage_string_fmt = 'Usage of {verbose_name}:'
