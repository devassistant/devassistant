import logging
import os
import sys

from devassistant.cli import argparse_generator
from devassistant import exceptions
from devassistant import logger
from devassistant import path_runner

class CliRunner(object):
    @classmethod
    def register_console_logging_handler(cls):
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logger.DevassistantClFormatter())
        console_handler.setLevel(logging.INFO)
        logger.logger.addHandler(console_handler)

    @classmethod
    def run_assistant(cls, assistant):
        cls.register_console_logging_handler()
        cls.inform_of_short_bin_names(sys.argv[0])
        ch = assistant.get_subassistant_tree()
        parsed_args = argparse_generator.ArgparseGenerator.generate_argument_parser(ch).parse_args()
        path = assistant.get_selected_subassistant_path(**vars(parsed_args))
        pr = path_runner.PathRunner(path, vars(parsed_args))
        try:
            pr.run()
        except exceptions.ExecutionException:
            # error is already logged, just catch it and silently exit here
            sys.exit(1)

    @classmethod
    def inform_of_short_bin_names(cls, binary):
        binary = os.path.splitext(os.path.basename(binary))[0]
        bin_mapping = {'devassistant': 'da',
                       'devassistant-modify': 'da-mod',
                       'devassistant-prepare': 'da-prep'}
        short = bin_mapping.get(binary)
        if short:
            msg = '"{short}" is the preffered way of running "{binary}".'.format(short=short,
                                                                                 binary=binary)
            logger.logger.info('*' * len(msg))
            logger.logger.info(msg)
            logger.logger.info('*' * len(msg))
