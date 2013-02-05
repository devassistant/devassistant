from devassistant import settings

class AssistantBase(object):
    """WARNING: if assigning subassistants in __init__, make sure to override it
    in subclass, so that it doesn't get inherited!"""
    # some of these values may be overriden by prepare
    # (e.g. needs_sudo, if prepare finds out that required package is not present)
    name = 'base'
    verbose_name = 'Base'
    needs_sudo = False

    args = []
    usage_string_fmt = '{verbose_name} Assistant parameters:'

    @property
    def usage(self):
        return self.usage_string_fmt.format(verbose_name=self.verbose_name)

    def get_subassistants(self):
        return []

    def get_subassistant_chain(self):
        if not '_chain' in dir(self):
            for subas in self.get_subassistants():
                subas_list = []
                if 'get_subassistants' in vars(self.__class__): # only non-inherited get_subassistants
                    for subas in self.get_subassistants():
                        subas_list.append(subas().get_subassistant_chain())
            self._chain = (self, subas_list)
        return self._chain

    def get_selected_subassistant_path(self, args_dict):
        """Recursively searches self._chain - has format of (Assistant: [list_of_subassistants]) -
        for specific path from first to last selected subassistants.
        Args:
            args_dict: dictionary containing names of the given assistants in form of
            {subassistant_0: 'name', subassistant_1: 'another_name', ...}
        Returns:
            List of subassistants objects from chain sorted from first to last.
        """
        path = [self]
        currently_searching = self._chain[1]
        # len(path) - 1 always points to next subassistant_N, so we can use it to control iteration
        while settings.SUBASSISTANT_N_STRING.format(len(path) - 1) in args_dict:
            for sa, subas_list in currently_searching:
                if sa.name == args_dict[settings.SUBASSISTANT_N_STRING.format(len(path) - 1)]:
                    currently_searching = subas_list
                    path.append(sa)
                    break # sorry if you shed a tear ;)

        return path

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
