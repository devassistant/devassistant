import logging

from devassistant.logger import logger

class TestLoggingHandler(logging.Handler):
    def __init__(self):
        super(TestLoggingHandler, self).__init__()
        self.msgs = []

    def emit(self, record):
        self.msgs.append((record.levelname, record.message))

    @classmethod
    def create_fresh_handler(cls):
        tlh = cls()
        logger.addHandler(tlh)
        return tlh
