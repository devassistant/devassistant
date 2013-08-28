import sys

from devassistant.gui import mainWindow

def run_gui():
    try:
        from gi.repository import Gtk
    except RuntimeError, e:
        print _("Developer Assistant GUI requires a running X server.")
        print "%s: %r" % (e.__class__.__name__, str(e))
        sys.exit(1)

    mainWindow.mainWindow()
