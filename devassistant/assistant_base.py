import os

from devassistant import exceptions
from devassistant import settings
from devassistant.command_helpers import ClHelper, PathHelper

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
    # we don't use this currently, so let's keep it commented so that we don't depend on jinja for no reason
    # _jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir))

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
        previous_subas_list = None
        currently_searching = self.get_subassistant_chain()[1]

        # len(path) - 1 always points to next subassistant_N, so we can use it to control iteration
        while settings.SUBASSISTANT_N_STRING.format(len(path) - 1) in kwargs and \
              kwargs[settings.SUBASSISTANT_N_STRING.format(len(path) - 1)]:
            for sa, subas_list in currently_searching:
                if sa.name == kwargs[settings.SUBASSISTANT_N_STRING.format(len(path) - 1)]:
                    currently_searching = subas_list
                    path.append(sa)
                    break # sorry if you shed a tear ;)

            if subas_list == previous_subas_list:
                raise exceptions.AssistantNotFoundException('No assistant {name} after path {path}.'.format(
                    name=kwargs[settings.SUBASSISTANT_N_STRING.format(len(path) - 1)],
                    path=path))
            previous_subas_list = subas_list

        return path

    def is_run_as_leaf(self, **kwargs):
        """Returns True if this assistant was run as last in path, False otherwise."""
        # find the last subassistant_N
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

    def _git_create_repo(self, path, gitignore, **kwargs):
        PathHelper.cp(gitignore, path)
        ClHelper.run_command('git init')
        ClHelper.run_command('git add .')
        ClHelper.run_command('git commit -m "Initial commit."')
