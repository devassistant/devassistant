import os

import jinja2
from github import Github
import getpass
import git
import sys
import plumbum

from devassistant import settings
from devassistant.logger import logger
from devassistant.command_helpers import PathHelper, ClHelper

class AssistantBase(object):
    """WARNING: if assigning subassistants in __init__, make sure to override it
    in subclass, so that it doesn't get inherited!"""
    # some of these values may be overriden by prepare
    # (e.g. needs_sudo, if prepare finds out that required package is not present)
    name = 'base'
    fullname = 'Base'
    needs_sudo = False

    args = []

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

    def _dot_devassistant_create(self, directory, **kwargs):
        self._dot_devassistant_path = os.path.join(directory, '.devassistant')
        f = open(self._dot_devassistant_path, 'w')
        # write path to this subassistant
        path = []
        i = 0
        while settings.SUBASSISTANT_N_STRING.format(i) in kwargs:
            path.append(kwargs[settings.SUBASSISTANT_N_STRING.format(i)])
            i += 1
        f.write('subassistant_path={0}'.format(' '.join(path)))
        f.close()

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

    def git_hub_registration_create(self, **kwargs):
        """Initialization repository on GitHub

        Raises:
            devassistant.exceptions.RunException containing the error message
        """
        gitname = kwargs['name']
        logger.info("Check whether repository is existing")
        """ Here we are checking whether we already created project structure or not
            This should be called after project creating
        """
        if PathHelper.path_exists('{0}/.git'.format(gitname)) == False:
            """
                This section is used by GitPython library
            """
            logger.info("Creating local repository")
            repo = git.Repo.init("{0}".format(gitname))
            repo.config_writer()
            logger.info(repo.git.status())
            for files in repo.untracked_files:
                repo.git.add(files)
            repo.git.commit(m="Initial commit")
            logger.info("Repository is not existing. Creating newer one")
            username = raw_input("Write your GitHub username:")
            password = getpass.getpass(prompt='Password:', stream=None)
            gh = Github(username,password)
            user = gh.get_user()
            if gitname in map(lambda x: x.name, user.get_repos()):
                logger.warning("Given repository is already existing on GiHub")
            else:
                user.create_repo(kwargs['name'])
        else:
            logger.info("Repository is already existing")
    def git_hub_remote(self, **kwargs):
        """Pushing all files to GitHub

        Raises:
            devassistant.exceptions.RunException containing the error message
        """
        gitname = kwargs['name']
        """ This section is used for parameter github: remote 
            which performs push operations to the server 
            In future there will be also operations like git add .
            and git commit -m "commit<date>" which will be done
            This has to be discussed whether all changes """
        try:
            result = ClHelper.run_command("git remote show origin",True,True)
            logger.info(result)
        except plumbum.ProcessExecutionError as e:
            """ This section is used for first synchronization
                between local and remote repository
            """
            try:
                ClHelper.run_command("git remote add origin https://github.com/{0}/{1}.git".format(kwargs['github'],kwargs['name']),True,True)
            except plumbum.ProcessExecutionError as ppe:
                """ This is empty session
                """
        """ This command will ensure that all changes will be pushed to the GitHub server
            """
        ClHelper.run_command("git push origin master",True,True)
