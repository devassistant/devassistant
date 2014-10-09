from devassistant.command_runners import CommandRunner
from devassistant.logger import logger

class LogCR(CommandRunner):
    @classmethod
    def matches(cls, c):
        return c.comm_type == 'log_i'

    @classmethod
    def run(cls, c):
        logger.info('Got you!')
        return (True, 'heee heee')
