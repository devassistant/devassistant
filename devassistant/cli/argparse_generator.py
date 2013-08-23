import argparse

from devassistant.cli import devassistant_argparse
from devassistant import command_helpers
from devassistant import settings

class ArgparseGenerator(object):
    subassistants_string = 'subassistants'
    subparsers_description = '''Following subassistants will help you with setting up your project.'''

    @classmethod
    def generate_argument_parser(cls, tree):
        cur_as, cur_subas = tree
        parser = devassistant_argparse.ArgumentParser(description=cur_as.description, argument_default=argparse.SUPPRESS)

        # add any arguments of the top assistant
        for arg in cur_as.args:
            arg.add_argument_to(parser)

        # add the argument for UI choice
        command_helpers.DialogHelper.get_argparse_argument().add_argument_to(parser)

        if cur_subas:
            # then add the subassistants as arguments
            subparsers = parser.add_subparsers(dest=settings.SUBASSISTANT_N_STRING.format('0'),
                                               title=cls.subassistants_string,
                                               description=cls.subparsers_description)
            # from Python 3.3, subparsers are optional by default => make them required
            subparsers.required=True
            for subas in sorted(cur_subas, key=lambda x: x[0].name):
                cls.add_subparsers_to(subas, subparsers, level=1)

        return parser

    @classmethod
    def add_subparsers_to(cls, assistant_tuple, parser, level):
        p = parser.add_parser(assistant_tuple[0].name, description=assistant_tuple[0].description, argument_default=argparse.SUPPRESS)
        for arg in assistant_tuple[0].args:
            arg.add_argument_to(p)

        if len(assistant_tuple[1]) > 0:
            subparsers = p.add_subparsers(dest=settings.SUBASSISTANT_N_STRING.format(level),
                                          title=cls.subassistants_string,
                                          description=cls.subparsers_description)
            for subas_tuple in sorted(assistant_tuple[1], key=lambda x: x[0].name):
                cls.add_subparsers_to(subas_tuple, subparsers, level + 1)
