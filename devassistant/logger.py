import logging
import os

import six

from devassistant import settings
from devassistant import utils

logger = logging.getLogger('devassistant')
logger.setLevel(logging.DEBUG)
logger_gui = logging.getLogger('devassistant-gui')
logger_gui.setLevel(logging.DEBUG)


class DevassistantClHandler(logging.StreamHandler):
    def emit(self, record):
        event_type = getattr(record, 'event_type', '')
        if event_type.startswith('dep_'):
            pass
        else:
            # can't use super() here, since in Python 2.6 StreamHandler is old style class
            logging.StreamHandler.emit(self, record)


class DevassistantClFormatter(logging.Formatter):
    def format(self, record):
        event_type = getattr(record, 'event_type', '')
        fmt_str = settings.LOG_FORMATS_MAP.get(event_type, None) or \
            settings.LOG_FORMATS_MAP['log_cmd']

        record_vars = vars(record)
        if six.PY2:
            if isinstance(record_vars['msg'], BaseException):
                record_vars['msg'] = record_vars['msg'].message
            if isinstance(record_vars['msg'], str):
                record_vars['msg'] = record_vars['msg'].decode(utils.defenc)
        return fmt_str.format(**record_vars)


class DevassistantClColorFormatter(DevassistantClFormatter):
    color_str = {'ERROR': u'\033[1;31m{0}\033[0m',
                 'WARNING': u'\033[1m{0}\033[0m'}

    def format(self, record):
        if record.levelname in self.color_str:
            return self.color_str[record.levelname].\
                format(DevassistantClFormatter.format(self, record))
        else:
            return DevassistantClFormatter.format(self, record)


def add_log_file_handler(log_file):
    # add logging handler to log current run into log file
    dirname = os.path.dirname(log_file)
    try:
        if not os.path.exists(dirname):
            os.makedirs(dirname)
    except (OSError, IOError):
        return False
    try:
        logger.addHandler(logging.FileHandler(log_file, 'w'))
    except (IOError, OSError):
        return False
    return True

def infolines(self, lines):
    '''info all the lines'''
    for line in lines:
        self.info(line)

logger.__class__.infolines = infolines
