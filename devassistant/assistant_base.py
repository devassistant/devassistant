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
    usage_string_fmt = 'Usage of {verbose_name}:'

    def get_subassistants(self):
        return []

    @classmethod
    def gather_subassistant_chain(cls):
        self_inst = cls()
        for subas in self_inst.get_subassistants():
            subas_list = []
            if 'get_subassistants' in vars(cls): # only non-inherited get_subassistants
                for subas in self_inst.get_subassistants():
                    subas_list.append(subas.gather_subassistant_chain())
        return (self_inst, subas_list)

    def errors(self, **kwargs):
        """Checks whether the command is doable, also checking the arguments
        passed as kwargs.
        Returns:
            List of errors as strings (empty list with no errors.
        """
        return []

    def prepare(self, **kwargs):
        """Prepares the object/gathers info needed to run (e.g. sets needs_sudo).
        """
        pass

    def run(self, **kwargs):
        """Actually carries out the command represented by this object.
        """
        pass
