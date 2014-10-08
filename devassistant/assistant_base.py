import os

from devassistant import exceptions
from devassistant import settings


class AssistantBase(object):
    """WARNING: if assigning subassistants in __init__, make sure to override it
    in subclass, so that it doesn't get inherited!"""
    # Some informations about assistant
    # These should all be present:
    name = 'base'
    fullname = 'Base'
    description = ''
    superassistant = None
    role = settings.DEFAULT_ASSISTANT_ROLE
    args = []
    project_type = []
    source_file = ''

    files_dir = os.path.join(os.path.dirname(__file__), 'data', 'files')

    def get_subassistant_classes(self):
        """Return list of classes that are subassistants of this assistant.

        Override in subclasses representing assistants written in Python

        Returns:
            list of classes that are subassistants of this assistant
        """
        return []

    def get_subassistants(self):
        """Return list of instantiated subassistants.

        Usually, this needs not be overriden in subclasses, you should just override
        get_subassistant_classes

        Returns:
            list of instantiated subassistants
        """
        if not hasattr(self, '_subassistants'):
            self._subassistants = []
            # we want to know, if type(self) defines 'get_subassistant_classes',
            # we don't want to inherit it from superclass (would cause recursion)
            if 'get_subassistant_classes' in vars(type(self)):
                for a in self.get_subassistant_classes():
                    self._subassistants.append(a())
        return self._subassistants

    def get_subassistant_tree(self):
        """Returns a tree-like structure representing the assistant hierarchy going down
        from this assistant to leaf assistants.

        For example: [(<This Assistant>,
                       [(<Subassistant 1>, [...]),
                        (<Subassistant 2>, [...])]
                      )]
        Returns:
            a tree-like structure (see above) representing assistant hierarchy going down
            from this assistant to leaf assistants
        """
        if '_tree' not in dir(self):
            subassistant_tree = []
            subassistants = self.get_subassistants()
            for subassistant in subassistants:
                subassistant_tree.append(subassistant.get_subassistant_tree())
            self._tree = (self, subassistant_tree)
        return self._tree

    def get_selected_subassistant_path(self, **kwargs):
        """Recursively searches self._tree - has format of (Assistant: [list_of_subassistants]) -
        for specific path from first to last selected subassistants.

        Args:
            kwargs: arguments containing names of the given assistants in form of
            subassistant_0 = 'name', subassistant_1 = 'another_name', ...
        Returns:
            list of subassistants objects from tree sorted from first to last
        """
        path = [self]
        previous_subas_list = None
        currently_searching = self.get_subassistant_tree()[1]

        # len(path) - 1 always points to next subassistant_N, so we can use it to control iteration
        while settings.SUBASSISTANT_N_STRING.format(len(path) - 1) in kwargs and \
                kwargs[settings.SUBASSISTANT_N_STRING.format(len(path) - 1)]:
            for sa, subas_list in currently_searching:
                if sa.name == kwargs[settings.SUBASSISTANT_N_STRING.format(len(path) - 1)]:
                    currently_searching = subas_list
                    path.append(sa)
                    break  # sorry if you shed a tear ;)

            if subas_list == previous_subas_list:
                raise exceptions.AssistantNotFoundException(
                    'No assistant {n} after path {p}.'.format(
                        n=kwargs[settings.SUBASSISTANT_N_STRING.format(len(path) - 1)],
                        p=path))
            previous_subas_list = subas_list

        return path

    def is_run_as_leaf(self, **kwargs):
        """Returns True if this assistant was run as last in path, False otherwise."""
        # find the last subassistant_N
        i = 0
        while i < len(kwargs):  # len(kwargs) is maximum of subassistant_N keys
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
            list of errors as strings (empty list with no errors)
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
