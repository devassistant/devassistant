from devassistant.cli import chain_handler
from devassistant.cli import path_runner
from devassistant import settings

class CliRunner(object):
    @classmethod
    def run_assistant(cls, assistant_cls):
        ch = chain_handler.ChainHandler(assistant_cls.gather_subassistant_chain())
        parsed_args = ch.get_argument_parser().parse_args()
        path = ch.get_path_to(getattr(parsed_args, settings.SUBASSISTANTS_STRING))
        pr = path_runner.PathRunner(path, parsed_args)
        pr.run()

