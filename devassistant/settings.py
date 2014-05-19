import logging
import os

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

SUBASSISTANT_PREFIX = 'subassistant'
SUBASSISTANT_N_STRING = 'subassistant_{0}'

DEPS_ONLY_FLAG = '--deps-only'

CACHE_FILE = os.path.expanduser('~/.devassistant/.cache.yaml')
DATA_DIRECTORIES = [os.path.join(os.path.dirname(__file__), 'data'),
                    '/usr/local/share/devassistant',
                    os.path.expanduser('~/.devassistant')]
if 'DEVASSISTANT_PATH' in os.environ:
    DATA_DIRECTORIES = os.environ['DEVASSISTANT_PATH'].split(':') + DATA_DIRECTORIES

ASSISTANT_ROLES = ['crt', 'mod', 'prep', 'task']
DEFAULT_ASSISTANT_ROLE = 'crt'

# system dependency types and package managers for various distros
# more distros can have the same system deptype, but different manager
SYSTEM_DEPTYPES_SHORTCUTS = {'rpm': ['fedora', 'red hat enterprise linux'],
                             'pacman': ['arch'],
                             # NOTE /etc/os-release has ID=gentoo,
                             # but platform.distribution reports "Gentoo Base System" string
                             'ebuild': ['gentoo', 'gentoo base system'],
                             'homebrew': ['darwin', 'OS X']}
