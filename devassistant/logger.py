import logging

from devassistant import settings

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
        return fmt_str.format(**vars(record))
