import logging
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
        ch = assistant.get_subassistant_chain()
        parsed_args = argparse_generator.ArgparseGenerator.generate_argument_parser(ch).parse_args()
        path = assistant.get_selected_subassistant_path(**vars(parsed_args))
        pr = path_runner.PathRunner(path, vars(parsed_args))
        try:
            pr.run()
        except exceptions.ExecutionException as ex:
            # error is already logged, just catch it and silently exit here
            sys.exit(1)
