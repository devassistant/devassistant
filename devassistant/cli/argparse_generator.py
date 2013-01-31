import argparse

from devassistant import settings

class ArgparseGenerator(object):
    @classmethod
    def generate_argument_parser(cls, chain):
        cur_as, cur_subas = chain
        parser = argparse.ArgumentParser(usage=cur_as.usage)

        # add any arguments of the top assistant
        for arg in cur_as.args:
            arg.add_argument_to(parser)

        # then add the subassistants as arguments
        subparsers = parser.add_subparsers(dest=settings.SUBASSISTANTS_STRING)
        for subas in cur_subas:
            cls.add_subparsers_to(subas, subparsers)

        return parser

    @classmethod
    def add_subparsers_to(cls, assistant_tuple, parser):
        p = parser.add_parser(assistant_tuple[0].name, usage=assistant_tuple[0].usage)
        for arg in assistant_tuple[0].args:
            arg.add_argument_to(p)

        if len(assistant_tuple[1]) > 0:
            subparsers = p.add_subparsers(dest=settings.SUBASSISTANTS_STRING)
            for subas_tuple in assistant_tuple[1]:
                cls.add_subparsers_to(subas_tuple, subparsers)
