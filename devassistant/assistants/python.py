from devassistant import argument
from devassistant import assistant_base
from devassistant import settings
from devassistant.logger import logger

from devassistant.command_helpers import PathHelper, RPMHelper, YUMHelper

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

    args = [argument.Argument('-n', '--name', required=True)]
    usage_string_fmt = 'Usage of {verbose_name}:'

    def errors(self, **kwargs):
        errors = []
        if PathHelper.path_exists(kwargs['name']):
            msg = 'Path "{0}" exists, cannot create a new Django project there.'.format(kwargs['name'])
            logger.error(msg)
            errors.append(msg)
        return errors

    def prepare(self, **kwargs):
        self.install_django = False
        logger.info('Checking for presence of python-django...')
        django_rpm = RPMHelper.is_rpm_present('python-django')
        if django_rpm:
            logger.info('Found %s', django_rpm)
        else:
            logger.info('Not found')
            self.install_django = True
            self.needs_sudo = True

    def run(self, **kwargs):
        if self.install_django:
            logger.info('Installing python-django...')
            YUMHelper.install('python-django')
            django_rpm = RPMHelper.is_rpm_present('python-django')
            logger.info('Installed %s', django_rpm)
