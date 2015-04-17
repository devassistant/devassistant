import logging
import os
import sys
import six

from devassistant import actions
from devassistant import bin
from devassistant.cli import argparse_generator
from devassistant import exceptions
from devassistant import logger
from devassistant import path_runner
from devassistant import settings
from devassistant import sigint_handler
from devassistant import utils


class CliRunner(object):
    cur_handler = None

    @classmethod
    def register_console_logging_handler(cls, lgr, level=logging.INFO):
        """Registers console logging handler to given logger."""
        console_handler = logger.DevassistantClHandler(sys.stdout)
        if console_handler.stream.isatty():
            console_handler.setFormatter(logger.DevassistantClColorFormatter())
        else:
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
        sigint_handler.override()
        # set settings.USE_CACHE before constructing parser, since constructing
        # parser requires loaded assistants
        settings.USE_CACHE = False if '--no-cache' in sys.argv else True
        cls.register_console_logging_handler(logger.logger)
        is_log_file = logger.add_log_file_handler(settings.LOG_FILE)
        if not is_log_file:
            logger.logger.warning("Could not create log file '{0}'.".format(settings.LOG_FILE))
        cls.inform_of_short_bin_name(sys.argv[0])
        top_assistant = bin.TopAssistant()
        tree = top_assistant.get_subassistant_tree()
        argparser = argparse_generator.ArgparseGenerator.\
            generate_argument_parser(tree, actions=actions.actions)
        parsed_args = vars(argparser.parse_args())

        parsed_args_decoded = dict()
        for k, v in parsed_args.items():
            parsed_args_decoded[k] = \
                v.decode(utils.defenc) if not six.PY3 and isinstance(v, str) else v
        parsed_args_decoded['__ui__'] = 'cli'

        if parsed_args.get('da_debug'):
            cls.change_logging_level(logging.DEBUG)

        # Prepare Action/PathRunner
        if actions.is_action_run(**parsed_args_decoded):
            to_run = actions.get_action_to_run(**parsed_args_decoded)(**parsed_args_decoded)
        else:
            parsed_args = cls.transform_executable_assistant_alias(parsed_args_decoded)
            path = top_assistant.get_selected_subassistant_path(**parsed_args_decoded)
            to_run = path_runner.PathRunner(path, parsed_args_decoded)

        try:
            to_run.run()
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

    @classmethod
    def transform_executable_assistant_alias(cls, parsed_args):
        key = settings.SUBASSISTANT_N_STRING.format(0)
        for assistant in [bin.CreatorAssistant, bin.TweakAssistant,
                          bin.PreparerAssistant, bin.ExtrasAssistant]:
            if parsed_args[key] in assistant.aliases:
                parsed_args[key] = assistant.name
        return parsed_args


if __name__ == '__main__':
    # this is here mainly because of utils.cl_string_from_da_eval
    # because it's the safest way to invoke DA on commandline
    # (invoking "da" binary is not safe because we can use os.chdir and so on)
    CliRunner.run()
