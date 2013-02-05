import os

import plumbum

from devassistant import argument
from devassistant import assistant_base
from devassistant.logger import logger

from devassistant.command_helpers import PathHelper, RPMHelper, YUMHelper

class PythonAssistant(assistant_base.AssistantBase):
    def get_subassistants(self):
        return [DjangoAssistant, FlaskAssistant]

    name = 'python'
    verbose_name = 'Python'

class DjangoAssistant(PythonAssistant):
    name = 'django'
    verbose_name = 'Django'

    args = [argument.Argument('-n', '--name',
                              required=True,
                              help='Name of the project (can also be full or relative path)')]

    usage_string_fmt = '{verbose_name} Assistant lets you create a Django project.'

    def errors(self, **kwargs):
        errors = []
        self.path = os.path.abspath(os.path.expanduser(kwargs['name']))

        path_exists = PathHelper.error_if_path_exists(self.path)
        if path_exists:
            errors.append(path_exists)
        return errors

    def dependencies(self, **kwargs):
        django_rpm = RPMHelper.is_rpm_present('python-django')
        if not django_rpm:
            YUMHelper.install('python-django')
        RPMHelper.was_rpm_installed('python-django')

    def run(self, **kwargs):
        django_admin = plumbum.local['django_admin']
        project_path, project_name = os.path.split(self.path)

        logger.info('Creating Django project {name} in {path}...'.format(path=project_path,
                                                                         name=project_name))
        PathHelper.mkdir_p(project_path)
        with plumbum.local.cwd(project_path):
            django_admin('startproject', project_name)
        logger.info('Django project {name} in {path} has been created.'.format(path=project_path,
                                                                               name=project_name))

class FlaskAssistant(PythonAssistant):
    name = 'flask'
    verbose_name = 'Flask'

    args = [argument.Argument('-n', '--name',
                              required=True,
                              help='Name of the project (can also be full or relative path)')]

    def errors(self, **kwargs):
        errors = []
        path_exists = PathHelper.error_if_path_exists(kwargs['name'])
        if path_exists:
            errors.append(path_exists)
        return errors

    def dependencies(self, **kwargs):
        to_install = []

        # TODO: this should be substituted by a yum group
        for pkg in ['python-flask', 'python-flask-sqlalchemy', 'python-flask-wtf']:
            if not RPMHelper.is_rpm_present(pkg):
                to_install = []

        if to_install:
            YUMHelper.install(*to_install)

        for pkg in to_install:
            RPMHelper.was_rpm_installed(pkg)

    def run(self, **kwargs):
        logger.info('Kickstarting a Flask project under {0}'.format(kwargs['name']))
        logger.info('Creating directory structure...')
        PathHelper.mkdir_p(kwargs['name'])
        PathHelper.mkdir_p('{0}/static'.format(kwargs['name']))
        PathHelper.mkdir_p('{0}/templates'.format(kwargs['name']))

        logger.info('Creating initial project files...')
        # the flask template doesn't in fact need rendering, so just copy it
        PathHelper.cp(os.path.join(os.path.dirname(__file__), '..', 'templates', 'python', 'flask'),
                      os.path.join(kwargs['name'], '__init__.py'))
