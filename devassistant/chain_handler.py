import argparse
from devassistant import settings

class ChainHandler(object):
    def __init__(self, chain):
        self.chain = chain

    def get_argument_parser(self):
        parser = argparse.ArgumentParser()
        cur_as, cur_subas = self.chain

        # add any arguments of the top assistant
        for arg in cur_as.args:
            arg.add_argument_to(parser)

        # then add the subassistants as arguments
        subparsers = parser.add_subparsers(dest=settings.SUBASSISTANTS_STRING)
        for subas in cur_subas:
            self.add_subparsers_to(subas, subparsers)

        return parser

    def add_subparsers_to(self, assistant_tuple, parser):
        p = parser.add_parser(assistant_tuple[0].name)
        for arg in assistant_tuple[0].args:
            arg.add_argument_to(p)

        if len(assistant_tuple[1]) > 0:
            subparsers = p.add_subparsers(dest=settings.SUBASSISTANTS_STRING)
            for subas_tuple in assistant_tuple[1]:
                self.add_subparsers_to(subas_tuple, subparsers)
