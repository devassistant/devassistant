import os
import signal

datadir = os.path.join(os.path.dirname(__file__), 'data')
cache = os.path.join(datadir, '.cache.yaml')
config = os.path.join(datadir, '.config')
lastrun = os.path.join(datadir, 'lastrun.log')

homedir_files = [cache, config, lastrun]

def before_all(context):
    context.dagui_scriptname = 'da-gui.py'
    context.dagui_scriptpath = os.path.abspath(context.dagui_scriptname)
    os.environ['DEVASSISTANT_NO_DEFAULT_PATH'] = '1'
    os.environ['DEVASSISTANT_PATH'] = datadir
    os.environ['DEVASSISTANT_HOME'] = datadir

def after_scenario(context, scenario):
    for f in homedir_files:
        if os.path.exists(f):
            os.remove(f)
    os.kill(context.dagui_pid, signal.SIGKILL)
