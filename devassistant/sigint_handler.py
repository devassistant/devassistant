import signal
import sys

from devassistant.logger import logger
from devassistant import package_managers


def override():
    def signal_handler(signal, frame):
        if package_managers.DependencyInstaller.install_lock:
            logger.warning('Can\'t interrupt dependency installation!')
        else:
            logger.info('DevAssistant received SIGINT, exiting ...')
            sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
