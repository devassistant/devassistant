import getpass
import glob
import os

import six

from devassistant import current_run
from devassistant import exceptions
from devassistant import settings
from devassistant import utils
from devassistant.command_helpers import ClHelper, DialogHelper
from devassistant.logger import logger


class GitHubAuth(object):
    """Only use the github_authenticated decorator from the class.
    The other methods should be consider private; they expect certain order of calling,
    so calling them ad-hoc may break something.
    """
    _user = None
    _token = None
    try:
        _gh_module = utils.import_module('github')
    except:
        _gh_module = None

    @classmethod
    def _github_token(cls, login):
        if not cls._token:
            try:
                cls._token = ClHelper.run_command("git config github.token.{login}".format(
                    login=login))
            except exceptions.ClException:
                pass  # token is not available yet

        return cls._token

    @classmethod
    def _get_github_user(cls, login):
        if not cls._user:
            try:
                # try logging with token
                token = cls._github_token(login)
                gh = cls._gh_module.Github(login_or_token=token)
                cls._user = gh.get_user()
                # try if the authentication was successful
                cls._user.login
            except cls._gh_module.GithubException:
                # if the token was set, it was wrong, so make sure it's reset
                cls._token = None
                # try login with username/password 3 times
                cls._user = cls._try_login_with_password_ntimes(login, 3)
                if cls._user is not None:
                    cls._github_create_auth()  # create auth for future use
        return cls._user

    @classmethod
    def _try_login_with_password_ntimes(cls, login, ntimes):
        user = None

        for i in range(0, ntimes):
            password = DialogHelper.ask_for_password(
                prompt='Github Password for {username}:'.format(username=login))

            # user pressed Ctrl + D
            if password is None:
                break

            gh = cls._gh_module.Github(login_or_token=login, password=password)
            user = gh.get_user()
            try:
                user.login
                break  # if user.login doesn't raise, authentication has been successful
            except cls._gh_module.GithubException as e:
                user = None
                msg = 'Wrong Github username or password; message from Github: {0}\n'.\
                    format(e.data.get('message', 'Unknown authentication error'))
                msg += 'Try again or press {0} to abort.'
                if current_run.UI == 'cli':
                    msg = msg.format('Ctrl + D')
                else:
                    msg = msg.format('"Cancel"')
                logger.warning(msg)

        return user

    @classmethod
    def _github_create_auth(cls):
        """ Store token into ~/.gitconfig.

        Note: this uses cls._user.get_authorizations(), which only works if cls._user
        was authorized by login/password, doesn't work for token auth (TODO: why?).
        If token is not defined then store it into ~/.gitconfig file
        """
        if not cls._token:
            try:
                auth = None
                for a in cls._user.get_authorizations():
                    if a.note == 'DevAssistant':
                        auth = a
                if not auth:
                    auth = cls._user.create_authorization(
                        scopes=['repo', 'user', 'admin:public_key'],
                        note="DevAssistant")
                ClHelper.run_command("git config --global github.token.{login} {token}".format(
                    login=cls._user.login,
                    token=auth.token))
                ClHelper.run_command("git config --global github.user.{login} {login}".format(
                    login=cls._user.login))
            except cls._gh_module.GithubException as e:
                logger.warning('Creating authorization failed: {0}'.format(e))

    @classmethod
    def _github_create_ssh_key(cls):
        """Creates a local ssh key, if it doesn't exist already, and uploads it to Github."""
        try:
            login = cls._user.login
            pkey_path = '{home}/.ssh/{keyname}'.format(home=os.path.expanduser('~'),
                        keyname=settings.GITHUB_SSH_KEYNAME.format(login=login))
            # generate ssh key only if it doesn't exist
            if not os.path.exists(pkey_path):
                ClHelper.run_command('ssh-keygen -t rsa -f {pkey_path}\
                                     -N \"\" -C \"DevAssistant\"'.\
                                     format(pkey_path=pkey_path))
            ClHelper.run_command('ssh-add {pkey_path}'.format(pkey_path=pkey_path))
            public_key = ClHelper.run_command('cat {pkey_path}.pub'.format(pkey_path=pkey_path))
            cls._user.create_key("DevAssistant", public_key)
        except exceptions.ClException as e:
            msg = 'Couldn\'t create a new ssh key: {e}'.format(e)
            raise exceptions.CommandException(msg)

    @classmethod
    def _create_ssh_config_entry(cls):
        # TODO: some duplication with _ssh_key_needs_config_entry, maybe refactor a bit
        ssh_config = os.path.expanduser('~/.ssh/config')
        fh = os.fdopen(os.open(ssh_config, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600), 'a')
        fh.write(settings.GITHUB_SSH_CONFIG.format(
                 login=cls._user.login,
                 keyname=settings.GITHUB_SSH_KEYNAME.format(login=cls._user.login)))
        fh.close()

    @classmethod
    def _github_ssh_key_exists(cls):
        """Returns True if any key on Github matches a local key, else False."""
        remote_keys = map(lambda k: k._key, cls._user.get_keys())
        found = False
        pubkey_files = glob.glob(os.path.expanduser('~/.ssh/*.pub'))
        for rk in remote_keys:
            for pkf in pubkey_files:
                local_key = open(pkf).read()
                # in PyGithub 1.23.0, remote key is an object, not string
                rkval = rk if isinstance(rk, six.string_types) else rk.value
                # don't use "==" because we have comments etc added in public_key
                if rkval in local_key:
                    found = True
                    break
        return found

    @classmethod
    def _ssh_key_needs_config_entry(cls):
        if getpass.getuser() != cls._user.login:
            ssh_config = os.path.expanduser('~/.ssh/config')
            user_github_string = 'github.com-{0}'.format(cls._user.login)
            needs_to_add_config_entry = True

            if os.path.isfile(ssh_config):
                fh = open(ssh_config)
                config_content = fh.read()
                if user_github_string in config_content:
                    needs_to_add_config_entry = False
                fh.close()
            return needs_to_add_config_entry
        return False

    @classmethod
    def github_authenticated(cls, func):
        """Does user authentication, creates SSH keys if needed and injects "_user" attribute
        into class/object bound to the decorated function.
        Don't call any other methods of this class manually, this should be everything you need.
        """
        def inner(func_cls, *args, **kwargs):
            if not cls._gh_module:
                logger.warning('PyGithub not installed, skipping Github auth procedures.')
            elif not func_cls._user:
                # authenticate user, possibly also creating authentication for future use
                func_cls._user = cls._get_github_user(kwargs['login'])
                if func_cls._user is None:
                    msg = 'Github authentication failed, skipping Github command.'
                    logger.warning(msg)
                    return (False, msg)
                # create an ssh key for pushing if we don't have one
                if not cls._github_ssh_key_exists():
                    cls._github_create_ssh_key()
                # next, create ~/.ssh/config entry for the key, if system username != GH login
                if cls._ssh_key_needs_config_entry():
                    cls._create_ssh_config_entry()
            return func(func_cls, *args, **kwargs)

        return inner
