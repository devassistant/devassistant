import argparse
import os
import sys

from devassistant import settings
from devassistant import utils

GUI_MESSAGE = "DevAssistant GUI requires a running X server."
GUI_MESSAGE_DISPLAY = "Environment variable DISPLAY is not set."


def run_gui():
    """
    Function for running DevAssistant GUI
    """
    try:
        from gi.repository import Gtk
    except ImportError as ie:
        pass
    except RuntimeError as e:
        sys.stderr.write(GUI_MESSAGE)
        sys.stderr.write("%s: %r" % (e.__class__.__name__, utils.exc_as_decoded_string(e)))
        sys.stderr.flush()
        sys.exit(1)

    if not os.environ.get('DISPLAY'):
        sys.stderr.write("%s %s" % (GUI_MESSAGE, GUI_MESSAGE_DISPLAY))
        sys.stderr.flush()
        sys.exit(1)

    parser = argparse.ArgumentParser(description='Run DevAssistant GUI.')
    utils.add_no_cache_argument(parser)
    # now we only have "--no-cache" argument, which we don't actually need to remember,
    #  see add_no_cache_argument help; so we only run parse_args to determine if
    #  the invocation was correct
    parser.parse_args()

    settings.USE_CACHE = False if '--no-cache' in sys.argv else True
    from devassistant.gui import main_window
    main_window.MainWindow()
