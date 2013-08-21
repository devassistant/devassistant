import os
GITHUB_SSH_CONFIG = '''
# devassistant config for user {login}
Host github.com-{login}
    HostName github.com
    User git
    IdentityFile ~/.ssh/{keyname}'''
GITHUB_SSH_KEYNAME = 'id_rsa_devassistant_{login}'
LOG_FORMATS_MAP = {'log_cmd': u'{levelname}: {msg}', 'cmd_call': u'[devassistant]$ {msg}', 'cmd_out': u'| {msg}'}
LOG_LEVELS_MAP = {'d': 'DEBUG', 'i': 'INFO', 'w': 'WARNING', 'e': 'ERROR', 'c': 'CRITICAL'}
SUBASSISTANT_PREFIX = 'subassistant'
SUBASSISTANT_N_STRING = 'subassistant_{0}'
UI_FLAG = '--ui'
DEPS_ONLY_FLAG = '--deps-only'
CACHE_FILE = os.path.expanduser('~/.devassistant/.cache.yaml')
DATA_DIRECTORIES = [os.path.join(os.path.dirname(__file__), 'data'),
                    '/usr/local/share/devassistant',
                    os.path.expanduser('~/.devassistant')]
ASSISTANT_ROLES=['creator', 'modifier', 'preparer']
