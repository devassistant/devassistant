from devassistant.command_runners import CommandRunner
from devassistant.logger import logger

class CR1(CommandRunner):
    @classmethod
    def matches(cls, c):
        return c.comm_type == 'barbarbar'

    @classmethod
    def run(cls, c):
        logger.info('CR1: Doing something ...')
        x = c.input_res + 'bar'
        return (True, x)


class CR2(CommandRunner):
    @classmethod
    def matches(cls, c):
        return c.comm_type == 'spamspamspam'

    @classmethod
    def run(cls, c):
        logger.info('CR2: Doing something ...')
        x = c.input_res + 'spam'
        return (True, x)
