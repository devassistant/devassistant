# -*- coding: utf-8 -*-
import io
import logging
import pytest

from devassistant.logger import logger, DevassistantClHandler, DevassistantClFormatter, \
                                DevassistantClColorFormatter
from flexmock import flexmock


class TestLogger(object):
    '''
    This class does not use sys.stdout as its default logging file as that proved
    to be difficult to implement given the magic py.test does with sys.stdout during testing.
    '''

    def setup_method(self, method):
        self.log = io.StringIO() # Necessary (see class description)
        self.console_handler = DevassistantClHandler(self.log)
        self.console_handler.setFormatter(DevassistantClFormatter())
        self.console_handler.setLevel(logging.INFO)
        logger.addHandler(self.console_handler)

    def teardown_method(self, method):
        logger.removeHandler(self.console_handler)

    def test_logger_basic(self):
        logger.info('info ...')
        assert self.log.getvalue() == 'INFO: info ...\n', ''

    @pytest.mark.parametrize(('level', 'formatter', 'output'), [
        ('error', DevassistantClFormatter, 'ERROR: {0}\n'),
        ('error', DevassistantClColorFormatter, '\033[1;31mERROR: {0}\033[0m\n'),
        ('warning', DevassistantClFormatter, 'WARNING: {0}\n'),
        ('warning', DevassistantClColorFormatter, '\033[1mWARNING: {0}\033[0m\n')
    ])
    def test_color_formatters(self, level, formatter, output):
        log_str = 'foo'
        self.console_handler.setFormatter(formatter())

        getattr(logger, level)(log_str) # e. g. logger.error(log_str)
        assert self.log.getvalue() == output.format(log_str)

    def test_unicode_chars(self):
        logger.info('ěšč')
        logger.info(u'čřž')
        assert self.log.getvalue() == u'INFO: ěšč\nINFO: čřž\n'
