import signal

from devassistant import package_managers

def signal_handler(signal, frame):
    import sys
    if package_managers.DependencyInstaller.install_lock:
        print('Can\'t interrupt dependency installation!')
    else:
        print('Devassistant received SIGINT, exiting...')
        sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

del signal
del signal_handler
