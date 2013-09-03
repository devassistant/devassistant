import logging
import os
import sys

from devassistant.actions import actions
from devassistant import bin
from devassistant.cli import argparse_generator
from devassistant import exceptions
from devassistant import logger
from devassistant import path_runner
from devassistant import settings

class CliRunner(object):
    @classmethod
    def register_console_logging_handler(cls):
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logger.DevassistantClFormatter())
        console_handler.setLevel(logging.INFO)
        logger.logger.addHandler(console_handler)

    @classmethod
    def run(cls):
        cls.register_console_logging_handler()
        cls.inform_of_short_bin_name(sys.argv[0])
        top_assistant = bin.TopAssistant()
        ch = top_assistant.get_subassistant_tree()
        argparser = argparse_generator.ArgparseGenerator.\
                        generate_argument_parser(ch, actions=actions)
        parsed_args = argparser.parse_args()
        first_subparser = vars(parsed_args)[settings.SUBASSISTANT_N_STRING.format(0)]
        if first_subparser in actions:
            to_run = actions[first_subparser]
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
        binary = os.path.splitext(os.path.basename(binary))[0]
        if binary != 'da':
            msg = '"da" is the preffered way of running "{binary}".'.format(binary=binary)
            logger.logger.info('*' * len(msg))
            logger.logger.info(msg)
            logger.logger.info('*' * len(msg))
