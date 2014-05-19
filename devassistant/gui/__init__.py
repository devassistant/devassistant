import sys

from devassistant.gui import main_window
from devassistant.gui import creator_window

def run_gui():
    try:
        from gi.repository import Gtk
    except RuntimeError as e:
        print("Developer Assistant GUI requires a running X server.")
        print("%s: %r" % (e.__class__.__name__, str(e)))
        sys.exit(1)

    main_window.MainWindow()

def run_yaml_gui():
    try:
        from gi.repository import Gtk
    except RuntimeError as e:
        print("Developer Assistant GUI requires a running X server.")
        print("%s: %r" % (e.__class__.__name__, str(e)))
        sys.exit(1)

    creator_window.CreatorWindow()
