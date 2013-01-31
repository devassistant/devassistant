import argparse

from devassistant import settings

class ChainHandler(object):
    def __init__(self, chain):
        self.chain = chain

    def get_argument_parser(self):
        cur_as, cur_subas = self.chain
        parser = argparse.ArgumentParser(usage=cur_as.usage)

        # add any arguments of the top assistant
        for arg in cur_as.args:
            arg.add_argument_to(parser)

        # then add the subassistants as arguments
        subparsers = parser.add_subparsers(dest=settings.SUBASSISTANTS_STRING)
        for subas in cur_subas:
            self.add_subparsers_to(subas, subparsers)

        return parser

    def add_subparsers_to(self, assistant_tuple, parser):
        p = parser.add_parser(assistant_tuple[0].name, usage=assistant_tuple[0].usage)
        for arg in assistant_tuple[0].args:
            arg.add_argument_to(p)

        if len(assistant_tuple[1]) > 0:
            subparsers = p.add_subparsers(dest=settings.SUBASSISTANTS_STRING)
            for subas_tuple in assistant_tuple[1]:
                self.add_subparsers_to(subas_tuple, subparsers)

    def get_path_to(self, name):
        return self._search_assistant_list(name, [self.chain])

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
