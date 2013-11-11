import logging
import os
import sys

from devassistant import actions
from devassistant import bin
from devassistant.cli import argparse_generator
from devassistant import exceptions
from devassistant import logger
from devassistant import path_runner
from devassistant import settings

class CliRunner(object):
    cur_handler = None

    @classmethod
    def register_console_logging_handler(cls, lgr, level=logging.INFO):
        """Registers console logging handler to given logger."""
        console_handler = logger.DevassistantClHandler(sys.stdout)
        console_handler.setFormatter(logger.DevassistantClFormatter())
        console_handler.setLevel(level)
        cls.cur_handler = console_handler
        lgr.addHandler(console_handler)

    @classmethod
    def change_logging_level(cls, level):
        cls.cur_handler.setLevel(level)

    @classmethod
    def run(cls):
        """Runs the whole cli:

        1. Registers console logging handler
        2. Creates argparser from all assistants and actions
        3. Parses args and decides what to run
        4. Runs a proper assistant or action
        """
        cls.register_console_logging_handler(logger.logger)
        cls.inform_of_short_bin_name(sys.argv[0])
        top_assistant = bin.TopAssistant()
        tree = top_assistant.get_subassistant_tree()
        argparser = argparse_generator.ArgparseGenerator.\
                        generate_argument_parser(tree, actions=actions.actions)
        parsed_args = argparser.parse_args()
        if parsed_args.da_debug:
            cls.change_logging_level(logging.DEBUG)
        if actions.is_action_run(**vars(parsed_args)):
            to_run = actions.get_action_to_run(**vars(parsed_args))
        else:
            path = top_assistant.get_selected_subassistant_path(**vars(parsed_args))
            to_run = path_runner.PathRunner(path, vars(parsed_args))
        try:
            to_run.run(**vars(parsed_args))
        except exceptions.ExecutionException:
            # error is already logged, just catch it and silently exit here
            sys.exit(1)

    @classmethod
    def inform_of_short_bin_name(cls, binary):
        """Historically, we had "devassistant" binary, but we chose to go with
        shorter "da". We still allow "devassistant", but we recommend using "da".
        """
        binary = os.path.splitext(os.path.basename(binary))[0]
        if binary != 'da':
            msg = '"da" is the preffered way of running "{binary}".'.format(binary=binary)
            logger.logger.info('*' * len(msg))
            logger.logger.info(msg)
            logger.logger.info('*' * len(msg))
