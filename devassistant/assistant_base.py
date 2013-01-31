import argparse

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

    def get_subassistant_path(self, name):
        return self._search_assistant_list(name, [self._chain])

    def _search_assistant_list(self, name, assistant_list):
        """Simple depth first search of assistant_list chain.
        Args:
            name: name of assistant to search for
            assistant_list: tuple containing assistant and list of its subassistants
        Returns:
            list representing the path from first assistant to assistant with given name
            or None if name is not found
        """
        for assistant, subas_list in assistant_list:
            if assistant.name == name:
                return [assistant]
            else:
                search = self._search_assistant_list(name, subas_list)
                if search:
                    result = [assistant]
                    result.extend(search)
                    return result

    def errors(self, **kwargs):
        """Checks whether the command is doable, also checking the arguments
        passed as kwargs. These are supposed to be non-recoverable problems,
        that will abort the whole operation.

        Returns:
            List of errors as strings (empty list with no errors).
        """
        return []

    def prepare(self, **kwargs):
        """Prepares the object/gathers info needed to run (e.g. sets needs_sudo).
        Errors should not be logged, but only raised, they shall be logged on higher level.

        Raises:
            devassistant.exceptions.PrepareException containing the error message
        """
        pass

    def run(self, **kwargs):
        """Actually carries out the command represented by this object.
        Errors should not be logged, but only raised, they shall be logged on higher level.

        Raises:
            devassistant.exceptions.RunException containing the error message
        """
        pass
