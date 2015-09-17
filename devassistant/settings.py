import logging
import os
import sys

GITHUB_SSH_CONFIG = '''
# devassistant config for user {login}
Host github.com-{login}
    HostName github.com
    User git
    IdentityFile ~/.ssh/{keyname}'''
GITHUB_SSH_KEYNAME = 'id_rsa_devassistant_{login}'

LOG_FORMATS_MAP = {'log_cmd': u'{levelname}: {msg}',
                   'cmd_call': u'[devassistant]$ {msg}',
                   'cmd_out': u'{msg}',
                   'cmd_retcode': u'> retcode: {msg}',
                   'sub_da': u'{msg}'}
LOG_LEVELS_MAP = {'d': 'DEBUG', 'i': 'INFO', 'w': 'WARNING', 'e': 'ERROR', 'c': 'CRITICAL'}
LOG_SHORT_TO_NUM_LEVEL = {}
for level_short, level_name in LOG_LEVELS_MAP.items():
    LOG_SHORT_TO_NUM_LEVEL[level_short] = getattr(logging, level_name)

LAST_LR_VAR = 'LAST_LRES'
LAST_R_VAR = 'LAST_RES'

ROOT_EXECUTABLE = '/usr/libexec/da_auth'

SUBASSISTANT_PREFIX = 'subassistant'
SUBASSISTANT_N_STRING = 'subassistant_{0}'

DEPS_ONLY_FLAG = '--deps-only'

# NOTE: data directories should always be absolute paths, since
# - theoretically, if DevAssistant would change working directory and *then* try to
#   load assistants, the relative path would point in an unwanted location
# - command runners should be allowed to rely on this (e.g. if we pass a file from files
#   section to Jinja2Runner, we need to make sure it's fullpath)

# Without DEVASSISTANT_NO_DEFAULT_PATH we need to load the defaults:
if 'DEVASSISTANT_NO_DEFAULT_PATH' not in os.environ:
    DATA_DIRECTORIES = [os.path.expanduser('~/.devassistant'),
                        '/usr/local/share/devassistant',
                        '/usr/share/devassistant/']

    # Remove ~/.devassistant for root:
    try:
        if os.geteuid() == 0:
            DATA_DIRECTORIES = DATA_DIRECTORIES[1:]
    except AttributeError:  # NotUNIX
        pass

    # DEVASSISTANT_HOME is ~/.devassistant for nonroot
    # or /usr/local/share/devassistant for root
    DEVASSISTANT_HOME = DATA_DIRECTORIES[0]
    # Distro directory is where e.g. RPM packages are installed, i.e. /usr/share/devassistant/
    DISTRO_DIRECTORY = DATA_DIRECTORIES[-1]
elif 'DEVASSISTANT_HOME' not in os.environ or 'DEVASSISTANT_PATH' not in os.environ:
    logging.error('Both DEVASSISTANT_HOME and DEVASSISTANT_PATH '
                  'must be defined with DEVASSISTANT_NO_DEFAULT_PATH')
    sys.exit(1)
else:
    DATA_DIRECTORIES = []
    DISTRO_DIRECTORY = ''

# And now regardless the previous if/else
if 'DEVASSISTANT_PATH' in os.environ:
    # Load new directories defined by user
    _extra_dirs = [os.path.abspath(os.path.expanduser(p))
        for p in os.environ['DEVASSISTANT_PATH'].split(':')]
    # If the user mentioned distro directory manually, remove it's stratus
    if DISTRO_DIRECTORY and DISTRO_DIRECTORY in _extra_dirs:
        DISTRO_DIRECTORY = ''
    # And prepend already defined directories
    DATA_DIRECTORIES = _extra_dirs + DATA_DIRECTORIES

# User can also redefine DEVASSISTANT_HOME
if 'DEVASSISTANT_HOME' in os.environ:
    DEVASSISTANT_HOME = os.path.abspath(os.path.expanduser(os.environ['DEVASSISTANT_HOME']))

# When DEVASSISTANT_NO_DEFAULT_PATH is used, do not install to DA_HOME, but first DATA_DIRECTORY
if 'DEVASSISTANT_NO_DEFAULT_PATH' in os.environ:
    INSTALL_DIRECTORY = DATA_DIRECTORIES[0]
else:
    INSTALL_DIRECTORY = DEVASSISTANT_HOME
    if DEVASSISTANT_HOME not in DATA_DIRECTORIES:
        DATA_DIRECTORIES.insert(0, DEVASSISTANT_HOME)

USE_CACHE = True
CACHE_FILE = os.path.join(DEVASSISTANT_HOME, '.cache.yaml')
CONFIG_FILE = os.path.join(DEVASSISTANT_HOME, '.config')
LOG_FILE = os.path.join(DEVASSISTANT_HOME, 'lastrun.log')

ASSISTANT_ROLES = ['crt', 'twk', 'prep', 'extra']
DEFAULT_ASSISTANT_ROLE = 'crt'

# system dependency types and package managers for various distros
# more distros can have the same system deptype, but different manager
SYSTEM_DEPTYPES_SHORTCUTS = {'rpm': ['fedora', 'red hat enterprise linux', 'redhat', 'rhel',
                                     'centos', 'suse'],
                             'pacman': ['arch'],
                             # NOTE /etc/os-release has ID=gentoo,
                             # but platform.distribution reports "Gentoo Base System" string
                             'ebuild': ['gentoo', 'gentoo base system'],
                             'homebrew': ['darwin', 'OS X']}

DAPI_API_URL = os.environ.get('DAPI_API_URL', 'https://dapi.devassistant.org/api/')
# TODO Maybe get a better address in the future
DAPI_API_MIRROR_URL = os.environ.get('DAPI_API_URL', 'https://mirror-devassistant.rhcloud.com/api/')
