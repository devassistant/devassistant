import plumbum
import signal

def signal_handler(signal, frame):
    import sys
    print('Devassistant received SIGINT, exiting...')
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

del signal
del signal_handler

# hack around https://github.com/bkabrda/devassistant/issues/52
plumbum.commands._safechars += '()'

del plumbum
