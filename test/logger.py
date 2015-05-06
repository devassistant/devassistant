import logging

from devassistant.logger import logger

class LoggingHandler(logging.Handler):
    def __init__(self):
        logging.Handler.__init__(self)
        self.msgs = []

    def emit(self, record):
        self.msgs.append((record.levelname, record.getMessage()))

    @classmethod
    def create_fresh_handler(cls):
        tlh = cls()
        logger.addHandler(tlh)
        return tlh
