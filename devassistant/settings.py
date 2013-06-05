COMMAND_LOG_STRING = u'[devassistant]$ {cmd}'
COMMAND_OUTPUT_STRING = u'| {line}'
GITHUB_SSH_CONFIG = '''
# devassistant config for user {login}
Host github.com-{login}
    HostName github.com
    User git
    IdentityFile ~/.ssh/{keyname}'''
GITHUB_SSH_KEYNAME = 'id_rsa_devassistant_{login}'
LOG_LEVELS_MAP = {'d': 'DEBUG', 'i': 'INFO', 'w': 'WARNING', 'e': 'ERROR', 'c': 'CRITICAL'}
SUBASSISTANT_PREFIX = 'subassistant'
SUBASSISTANT_N_STRING = 'subassistant_{0}'
