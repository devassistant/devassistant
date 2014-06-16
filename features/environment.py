import os
import signal

def before_all(context):
    context.dagui_scriptname = 'da-gui.py'
    context.dagui_scriptpath = os.path.abspath(context.dagui_scriptname)
    os.environ['DEVASSISTANT_PATH'] = os.path.join(os.path.dirname(__file__), 'data')

def after_scenario(context, scenario):
    os.kill(context.dagui_pid, signal.SIGKILL)
