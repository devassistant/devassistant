import getpass
import os
import sys

import github
import jinja2
import plumbum

from devassistant import exceptions
from devassistant import settings
from devassistant.logger import logger
from devassistant.command_helpers import ClHelper, PathHelper, RPMHelper, YUMHelper

class AssistantBase(object):
    """WARNING: if assigning subassistants in __init__, make sure to override it
    in subclass, so that it doesn't get inherited!"""
    # Some informations about assistant
    # These are mandatory:
    name = 'base'
    fullname = 'Base'

    # These are optional:
    description = ''
    args = []
    repo = []

    template_dir = os.path.join(os.path.dirname(__file__), 'templates')

    # don't override these, used internally
    _dot_devassistant_path = None
    _jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir))

    def get_subassistants(self):
        return []

    def get_subassistant_chain(self):
        if not '_chain' in dir(self):
            subas_list = []
            if 'get_subassistants' in vars(self.__class__): # only non-inherited get_subassistants
                for subas in self.get_subassistants():
                    subas_list.append(subas().get_subassistant_chain())
            self._chain = (self, subas_list)
        return self._chain

    def get_selected_subassistant_path(self, **kwargs):
        """Recursively searches self._chain - has format of (Assistant: [list_of_subassistants]) -
        for specific path from first to last selected subassistants.
        Args:
            kwargs: arguments containing names of the given assistants in form of
            subassistant_0 = 'name', subassistant_1 = 'another_name', ...
        Returns:
            List of subassistants objects from chain sorted from first to last.
        """
        path = [self]
        currently_searching = self.get_subassistant_chain()[1]
        # len(path) - 1 always points to next subassistant_N, so we can use it to control iteration
        while settings.SUBASSISTANT_N_STRING.format(len(path) - 1) in kwargs and \
              kwargs[settings.SUBASSISTANT_N_STRING.format(len(path) - 1)]:
            for sa, subas_list in currently_searching:
                if sa.name == kwargs[settings.SUBASSISTANT_N_STRING.format(len(path) - 1)]:
                    currently_searching = subas_list
                    path.append(sa)
                    break # sorry if you shed a tear ;)

        return path

    def is_run_as_leaf(self, **kwargs):
        """Returns True if this assistant was run as last in path, False otherwise."""
        # find the last subassistant_N
        leaf_class = None
        i = 0
        while i < len(kwargs): # len(kwargs) is maximum of subassistant_N keys
            if settings.SUBASSISTANT_N_STRING.format(i) in kwargs:
                leaf_name = kwargs[settings.SUBASSISTANT_N_STRING.format(i)]
            i += 1

        return self.name == leaf_name

    def errors(self, **kwargs):
        """Checks whether the command is doable, also checking the arguments
        passed as kwargs. These are supposed to be non-recoverable problems,
        that will abort the whole operation.
        Errors should not be logged, only returned.

        Returns:
            List of errors as strings (empty list with no errors).
        """
        return []

    def dependencies(self, **kwargs):
        """Installs dependencies for this assistant.

        Raises:
            devassistant.exceptions.DependencyException containing the error message
        """
        pass

    def run(self, **kwargs):
        """Actually carries out the command represented by this object.
        Errors should not be logged, but only raised, they shall be logged on higher level.

        Raises:
            devassistant.exceptions.RunException containing the error message
        """
        pass

    def _install_dependencies(self, *dep_list, **kwargs):
        to_install = []

        for dep in dep_list:
            if dep.startswith('@'):
                if not YUMHelper.is_group_installed(dep):
                    to_install.append(dep)
            else:
                if not RPMHelper.is_rpm_installed(dep):
                    to_install.append(dep)

        if to_install: # only invoke YUM if we actually have something to install
            if not YUMHelper.install(*to_install):
                raise exceptions.RunException('Failed to install: {0}'.format(' '.join(to_install)))

        for pkg in to_install:
            RPMHelper.was_rpm_installed(pkg)

    def _git_create_repo(self, path, gitignore, **kwargs):
        PathHelper.cp(gitignore, path)
        with plumbum.local.cwd(os.path.abspath(os.path.expanduser(path))):
            ClHelper.run_command('git init')
            ClHelper.run_command('git add .')
            ClHelper.run_command('git commit -m "Initial commit."')

    def _github_username(self, **kwargs):
        return kwargs['github'] or getpass.getuser()

    def _github_reponame(self, **kwargs):
        """Extracts reponame from name, which is possibly a path."""
        return os.path.basename(kwargs['name'])

    def _github_create_repo(self, **kwargs):
        """Create repo on GitHub.

        If repository already exists then RunException will be raised.

        Raises:
            devassistant.exceptions.RunException on error
        """
        username = self._github_username(**kwargs)
        reponame = self._github_reponame(**kwargs)
        password = getpass.getpass(prompt='GitHub password:', stream=None)

        gh = github.Github(username, password)
        user = gh.get_user()
        try:
            if reponame in map(lambda x: x.name, user.get_repos()):
                logger.warning("Repository already exists on GiHub.")
            else:
                user.create_repo(reponame)
        except github.GithubException as e:
            raise exceptions.RunException('GitHub error: {0}'.format(e))

    def _github_push(self, **kwargs):
        """Add a remote and push to GitHub.

        Raises:
            devassistant.exceptions.RunException on error
        """
        username = self._github_username(**kwargs)
        reponame = self._github_reponame(**kwargs)
        has_remote = False

        try:
            result = ClHelper.run_command("git remote show origin")
            has_remote = True
        except plumbum.ProcessExecutionError as e:
            pass

        if not has_remote:
            try:
                ClHelper.run_command("git remote add origin https://github.com/{0}/{1}.git".format(username, reponame), True, True)
            except plumbum.ProcessExecutionError as e:
                pass # TODO: what exactly happens here?

        ClHelper.run_command("git push origin master", True, True)

    def _github_create_and_push(self, **kwargs):
        with plumbum.local.cwd(os.path.abspath(os.path.expanduser(kwargs['name']))):
            ClHelper.run_command('cd {0}'.format(os.path.abspath(os.path.expanduser(kwargs['name']))))
            logger.info('Registering your project on GitHub as {0}/{1}...'.format(self._github_username(**kwargs),
                                                                                  self._github_reponame(**kwargs)))
            self._github_create_repo(**kwargs)
            logger.info('Pushing your project to the new GitHub repository...')
            self._github_push(**kwargs)
            logger.info('GitHub repository was created and source code pushed.')
