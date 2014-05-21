import logging
import sys

from devassistant.logger import logger, DevassistantClHandler, DevassistantClFormatter


class TestLogger(object):
    # TODO: do more sophisticated tests, e.g. for logging formats of DevassistantClFormatter
    def test_logger_basic(self, capsys):
        console_handler = DevassistantClHandler(sys.stdout)
        console_handler.setFormatter(DevassistantClFormatter())
        console_handler.setLevel(logging.INFO)

        logger.addHandler(console_handler)

        # just test that logging works...
        logger.info('info ...')
        assert capsys.readouterr() == ('INFO: info ...\n', '')
