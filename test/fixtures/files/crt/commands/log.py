from devassistant.command_runners import CommandRunner
from devassistant.logger import logger

class LogCR(CommandRunner):
    @classmethod
    def matches(cls, c):
        return c.comm_type == 'log_i'

    def run(self):
        logger.info('Got you!')
        return (True, 'heee heee')
