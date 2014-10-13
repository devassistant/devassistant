import os
import sys


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
        sys.stderr.write("%s: %r" % (e.__class__.__name__, str(e)))
        sys.stderr.flush()
        sys.exit(1)

    if not os.environ.get('DISPLAY'):
        sys.stderr.write("%s %s" % (GUI_MESSAGE, GUI_MESSAGE_DISPLAY))
        sys.stderr.flush()
        sys.exit(1)
    from devassistant.gui import main_window
    main_window.MainWindow()
