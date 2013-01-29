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

    def get_argument_parser(self):
        parser = argparse.ArgumentParser(usage=self.usage_string_fmt.format(verbose_name=self.verbose_name))
        for arg in self.args:
            if not settings.SUBASSISTANTS_STRING in arg.flags:
                arg.add_argument_to(parser)

        subparsers = parser.add_subparsers()
        for subs_cls in self.get_subassistant_classes():
            subs_cls().add_subparsers_to(subparsers)

        return parser

    def add_subparsers_to(self, parser):
        p = parser.add_parser(self.name)
        for arg in self.args:
            if not settings.SUBASSISTANTS_STRING in arg.flags:
                arg.add_argument_to(p)

        subs_classes = self.get_subassistant_classes()
        if subs_classes:
            subparsers = p.add_subparsers()
            for subs_cls in subs_classes:
                subs_cls().add_subparsers_to(subparsers)

    def get_subassistant_classes(self):
        subas_cls_list = []

        for arg in self.args:
            if settings.SUBASSISTANTS_STRING in arg.flags:
                for k, v in arg.subassistants.items():
                    subas_cls_list.append(v)
        return subas_cls_list

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
