from devassistant.command_runners import CommandRunner
from devassistant.logger import logger

class CR1(CommandRunner):
    @classmethod
    def matches(cls, c):
        return c.comm_type == 'barbarbar'

    def run(self):
        logger.info('CR1: Doing something ...')
        x = self.c.input_res + 'bar'
        return (True, x)


class CR2(CommandRunner):
    @classmethod
    def matches(cls, c):
        return c.comm_type == 'spamspamspam'

    def run(self):
        logger.info('CR2: Doing something ...')
        x = self.c.input_res + 'spam'
        return (True, x)
