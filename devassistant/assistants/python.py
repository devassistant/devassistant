import os

import plumbum

from devassistant import argument
from devassistant import assistant_base
from devassistant import settings
from devassistant.logger import logger

from devassistant.command_helpers import PathHelper, RPMHelper, YUMHelper

class PythonAssistant(assistant_base.AssistantBase):
    def get_subassistants(self):
        return [DjangoAssistant, FlaskAssistant]

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

    django_admin = plumbum.local['django_admin']

    def errors(self, **kwargs):
        errors = []
        path_exists = PathHelper.error_if_path_exists(kwargs['name'])
        if path_exists:
            errors.append(path_exists)
        return errors

    def prepare(self, **kwargs):
        self.install_django = False
        django_rpm = RPMHelper.is_rpm_present('python-django')
        if not django_rpm:
            self.install_django = True
            self.needs_sudo = True

    def run(self, **kwargs):
        if self.install_django:
            logger.info('Installing python-django...')
            YUMHelper.install('python-django')
            django_rpm = RPMHelper.was_rpm_installed('python-django')

        self.django_admin('startproject', kwargs['name'])

class FlaskAssistant(PythonAssistant):
    name = 'flask'
    verbose_name = 'Flask'

    args = [argument.Argument('-n', '--name', required=True)]
    usage_string_fmt = 'Usage of {verbose_name}:'

    def errors(self, **kwargs):
        errors = []
        path_exists = PathHelper.error_if_path_exists(kwargs['name'])
        if path_exists:
            errors.append(path_exists)
        return errors

    def prepare(self, **kwargs):
        self.to_install = []

        # TODO: this should be substituted by a yum group
        for pkg in ['python-flask', 'python-flask-sqlalchemy', 'python-flask-wtf']:
            if not RPMHelper.is_rpm_present(pkg):
                self.to_install = []

        if self.to_install:
            self.needs_sudo = True

    def run(self, **kwargs):
        if self.to_install:
            YUMHelper.install(*self.to_install)
            for pkg in self.to_install:
                RPMHelper.was_rpm_installed(pkg)

        logger.info('Kickstarting a Flask project under {0}'.format(kwargs['name']))
        logger.info('Creating directory structure...')
        PathHelper.mkdir_p(kwargs['name'])
        PathHelper.mkdir_p('{0}/static'.format(kwargs['name']))
        PathHelper.mkdir_p('{0}/templates'.format(kwargs['name']))

        logger.info('Creating initial project files...')
        # the flask template doesn't in fact need rendering, so just copy it
        PathHelper.cp(os.path.join(os.path.dirname(__file__), '..', 'templates', 'python', 'flask'),
                      os.path.join(kwargs['name'], '__init__.py'))
