import argparse

from devassistant.cli import devassistant_argparse
from devassistant import command_helpers
from devassistant import settings

class ArgparseGenerator(object):
    subparsers_str = 'subassistants'
    subparsers_desc = '''Following subassistants will help you with setting up your project.'''

    @classmethod
    def generate_argument_parser(cls, tree, actions=[]):
        cur_as, cur_subas = tree
        parser = devassistant_argparse.ArgumentParser(argument_default=argparse.SUPPRESS,
                                                      usage=argparse.SUPPRESS,
                                                      add_help=False)

        # add any arguments of the top assistant
        for arg in cur_as.args:
            arg.add_argument_to(parser)

        # add the argument for UI choice
        command_helpers.DialogHelper.get_argparse_argument().add_argument_to(parser)

        if cur_subas or actions:
            # then add the subassistants as arguments
            subparsers = parser.add_subparsers(dest=settings.SUBASSISTANT_N_STRING.format('0'))
            # from Python 3.3, subparsers are optional by default => make them required
            subparsers.required=True
            for subas in sorted(cur_subas, key=lambda x: x[0].name):
                cls.add_subassistants_to(subparsers, subas, level=1)

            for action_name, action in sorted(actions.items()):
                cls.add_action_to(subparsers, action)

        return parser

    @classmethod
    def add_subassistants_to(cls, parser, assistant_tuple, level):
        p = parser.add_parser(assistant_tuple[0].name,
                              description=assistant_tuple[0].description,
                              argument_default=argparse.SUPPRESS)
        for arg in assistant_tuple[0].args:
            arg.add_argument_to(p)

        if len(assistant_tuple[1]) > 0:
            subparsers = p.add_subparsers(dest=settings.SUBASSISTANT_N_STRING.format(level),
                                          title=cls.subparsers_str,
                                          description=cls.subparsers_desc)
            for subas_tuple in sorted(assistant_tuple[1], key=lambda x: x[0].name):
                cls.add_subassistants_to(subparsers, subas_tuple, level + 1)

    @classmethod
    def add_action_to(cls, parser, action):
        p = parser.add_parser(action.name,
                              description=action.description,
                              argument_default=argparse.SUPPRESS)

        for arg in action.args:
            arg.add_argument_to(p)
