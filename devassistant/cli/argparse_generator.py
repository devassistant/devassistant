import argparse

from devassistant.cli import devassistant_argparse
from devassistant import settings


class ArgparseGenerator(object):
    subparsers_str = 'subassistants'
    subparsers_desc = '''Following subassistants will help you with setting up your project.'''
    subparsers_no_avail = 'No subasistants are available. Please install ' +\
        '"assistants" package first.'
    subactions_str = 'subactions'
    subactions_desc = 'This action has following subactions.'

    @classmethod
    def generate_argument_parser(cls, tree, actions={}):
        """Generates argument parser for given assistant tree and actions.

        Args:
            tree: assistant tree as returned by
                  devassistant.assistant_base.AssistantBase.get_subassistant_tree
            actions: dict mapping actions (devassistant.actions.Action subclasses) to their
                     subaction dicts
        Returns:
            instance of devassistant_argparse.ArgumentParser (subclass of argparse.ArgumentParser)
        """
        cur_as, cur_subas = tree
        parser = devassistant_argparse.ArgumentParser(argument_default=argparse.SUPPRESS,
                                                      usage=argparse.SUPPRESS,
                                                      add_help=False)

        cls.add_default_arguments_to(parser)

        # add any arguments of the top assistant
        for arg in cur_as.args:
            arg.add_argument_to(parser)

        if cur_subas or actions:
            # then add the subassistants as arguments
            subparsers = parser.add_subparsers(dest=settings.SUBASSISTANT_N_STRING.format('0'))
            # from Python 3.3, subparsers are optional by default => make them required
            subparsers.required = True
            for subas in sorted(cur_subas, key=lambda x: x[0].name):
                for alias in [subas[0].name] + getattr(subas[0], 'aliases', []):
                    cls.add_subassistants_to(subparsers, subas, level=1, alias=alias)

            for action, subactions in sorted(actions.items(), key=lambda x: x[0].name):
                cls.add_action_to(subparsers, action, subactions, level=1)

        return parser

    @classmethod
    def add_default_arguments_to(cls, parser):
        # add --debug to the top parser (GUI does this completely differently)
        parser.add_argument('--debug',
                            help='Show debug output (may be a verbose a lot!).',
                            action='store_true',
                            dest='da_debug',
                            default=False)
        # TODO: should gui also get --no-cache?
        # This really only stores the True/False value. We need to set
        # current_run.USE_CACHE before we create the parser, but for creating
        # the parser, we need to load assistants. That means we set
        # current_run.USE_CACHE in cli_runner according to sys.argv.
        parser.add_argument('--no-cache',
                            help='Don\'t use assistants cache (useful for debugging).',
                            action='store_true',
                            dest='da_no_cache',
                            default=False)

    @classmethod
    def add_subassistants_to(cls, parser, assistant_tuple, level, alias=None):
        """Adds assistant from given part of assistant tree and all its subassistants to
        a given argument parser.

        Args:
            parser: instance of devassistant_argparse.ArgumentParser
            assistant_tuple: part of assistant tree (see generate_argument_parser doc)
            level: level of subassistants that given assistant is at
        """
        name = alias or assistant_tuple[0].name
        p = parser.add_parser(name,
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
        elif level == 1:
            subparsers = p.add_subparsers(dest=settings.SUBASSISTANT_N_STRING.format(level),
                                          title=cls.subparsers_str,
                                          description=cls.subparsers_no_avail)

    @classmethod
    def add_action_to(cls, parser, action, subactions, level):
        """Adds given action to given parser

        Args:
            parser: instance of devassistant_argparse.ArgumentParser
            action: devassistant.actions.Action subclass
            subactions: dict with subactions - {SubA: {SubB: {}}, SubC: {}}
        """
        p = parser.add_parser(action.name,
                              description=action.description,
                              argument_default=argparse.SUPPRESS)
        for arg in action.args:
            arg.add_argument_to(p)

        if subactions:
            subparsers = p.add_subparsers(dest=settings.SUBASSISTANT_N_STRING.format(level),
                                          title=cls.subactions_str,
                                          description=cls.subactions_desc)
            for subact, subsubacts in sorted(subactions.items(), key=lambda x: x[0].name):
                cls.add_action_to(subparsers, subact, subsubacts, level + 1)
