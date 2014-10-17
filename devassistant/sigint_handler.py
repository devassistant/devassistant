import signal
import sys

from devassistant.logger import logger
from devassistant import package_managers
from devassistant import utils


def override():
    def signal_handler(signal, frame):
        if package_managers.DependencyInstaller.install_lock:
            logger.warning('Can\'t interrupt dependency installation!')
        else:
            logger.info('DevAssistant received SIGINT, exiting ...')
            utils.run_exitfuncs()
            sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
