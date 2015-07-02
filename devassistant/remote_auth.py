import getpass
import glob
import io
import os

import six

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
        _gh_exceptions = utils.import_module('github.GithubException')

    except:
        _gh_module = None
        _gh_exceptions = None

    @classmethod
    def _github_token(cls, login):
        if not cls._token:
            try:
                cls._token = ClHelper.run_command("git config github.token.{login}".format(
                    login=login), log_secret=True)
            except exceptions.ClException:
                pass  # token is not available yet

        return cls._token

    @classmethod
    def _get_github_user(cls, login, ui):
        if not cls._github_token(login):
            cls._user = cls._try_login_with_password_ntimes(login, 3, ui)
        else:
            try: # try logging with token
                token = cls._github_token(login)
                gh = cls._gh_module.Github(login_or_token=token)
                user = gh.get_user()
                user.login # throws unless the authentication was successful
                cls._user = user
            except cls._gh_module.GithubException:
                # if the token was set, it was wrong, so make sure it's reset
                cls._token = None
                cls._user = cls._try_login_with_password_ntimes(login, 3, ui)

        if cls._token is None:
            cls._github_create_authorization(ui)

        return cls._user

    @classmethod
    def _github_create_authorization(cls, ui):
        try:
            cls._user.login
            cls._github_create_simple_authorization()
        except cls._gh_exceptions.TwoFactorException:
            cls._github_create_twofactor_authorization(ui)
        except cls._gh_exceptions.GithubException:
            raise

    @classmethod
    def _try_login_with_password_ntimes(cls, login, ntimes, ui):
        user = None

        for i in range(0, ntimes):
            password = DialogHelper.ask_for_password(
                ui, prompt='Github Password for {username}:'.format(username=login))

            # user pressed Ctrl + D
            if password is None:
                break

            gh = cls._gh_module.Github(login_or_token=login, password=password)
            user = gh.get_user()
            try:
                user.login
                break # if user.login doesn't raise, authentication has been successful
            except cls._gh_exceptions.TwoFactorException:
                break # two-factor auth is used
            except cls._gh_module.GithubException as e:
                user = None
                msg = 'Wrong Github username or password; message from Github: {0}\n'.\
                    format(e.data.get('message', 'Unknown authentication error'))
                msg += 'Try again or press {0} to abort.'
                if ui == 'cli':
                    msg = msg.format('Ctrl + D')
                else:
                    msg = msg.format('"Cancel"')
                logger.warning(msg)

        return user

    @classmethod
    def _github_create_twofactor_authorization(cls, ui):
        """Create an authorization for a GitHub user using two-factor
           authentication. Unlike its non-two-factor counterpart, this method
           does not traverse the available authentications as they are not
           visible until the user logs in.

           Please note: cls._user's attributes are not accessible until the
           authorization is created due to the way (py)github works.
        """
        try:
            try: # This is necessary to trigger sending a 2FA key to the user
                auth = cls._user.create_authorization()
            except cls._gh_exceptions.GithubException:
                onetime_pw = DialogHelper.ask_for_password(ui, prompt='Your one time password:')
                auth = cls._user.create_authorization(scopes=['repo', 'user', 'admin:public_key'],
                                            note="DevAssistant",
                                            onetime_password=onetime_pw)
                cls._user = cls._gh_module.Github(login_or_token=auth.token).get_user()
                logger.debug('Two-factor authorization for user "{0}" created'.format(cls._user.login))
                cls._github_store_authorization(cls._user, auth)
                logger.debug('Two-factor authorization token stored')
        except cls._gh_exceptions.GithubException as e:
            logger.warning('Creating two-factor authorization failed: {0}'.format(e))


    @classmethod
    def _github_create_simple_authorization(cls):
        """Create a GitHub authorization for the given user in case they don't
           already have one.
        """
        try:
            auth = None
            for a in cls._user.get_authorizations():
                if a.note == 'DevAssistant':
                    auth = a
            if not auth:
                auth = cls._user.create_authorization(
                    scopes=['repo', 'user', 'admin:public_key'],
                    note="DevAssistant")
                cls._github_store_authorization(cls._user, auth)
        except cls._gh_exceptions.GithubException as e:
            logger.warning('Creating authorization failed: {0}'.format(e))

    @classmethod
    def _github_store_authorization(cls, user, auth):
        """Store an authorization token for the given GitHub user in the git
           global config file.
        """
        ClHelper.run_command("git config --global github.token.{login} {token}".format(
            login=user.login, token=auth.token), log_secret=True)
        ClHelper.run_command("git config --global github.user.{login} {login}".format(
            login=user.login))

    @classmethod
    def _start_ssh_agent(cls):
        """Starts ssh-agent and returns the environment variables related to it"""
        env = dict()
        stdout = ClHelper.run_command('ssh-agent -s')
        lines = stdout.split('\n')
        for line in lines:
            if not line or line.startswith('echo '):
                continue
            line = line.split(';')[0]
            parts = line.split('=')
            if len(parts) == 2:
                env[parts[0]] = parts[1]
        return env

    @classmethod
    def _github_create_ssh_key(cls):
        """Creates a local ssh key, if it doesn't exist already, and uploads it to Github."""
        try:
            login = cls._user.login
            pkey_path = '{home}/.ssh/{keyname}'.format(
                home=os.path.expanduser('~'),
                keyname=settings.GITHUB_SSH_KEYNAME.format(login=login))
            # generate ssh key only if it doesn't exist
            if not os.path.exists(pkey_path):
                ClHelper.run_command('ssh-keygen -t rsa -f {pkey_path}\
                                     -N \"\" -C \"DevAssistant\"'.
                                     format(pkey_path=pkey_path))
            try:
                ClHelper.run_command('ssh-add {pkey_path}'.format(pkey_path=pkey_path))
            except exceptions.ClException:
                # ssh agent might not be running
                env = cls._start_ssh_agent()
                ClHelper.run_command('ssh-add {pkey_path}'.format(pkey_path=pkey_path), env=env)
            public_key = ClHelper.run_command('cat {pkey_path}.pub'.format(pkey_path=pkey_path))
            cls._user.create_key("DevAssistant", public_key)
        except exceptions.ClException as e:
            msg = 'Couldn\'t create a new ssh key: {0}'.format(e)
            raise exceptions.CommandException(msg)

    @classmethod
    def _create_ssh_config_entry(cls):
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
                local_key = io.open(pkf, encoding='utf-8').read()
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
                login = kwargs['login'].encode(utils.defenc) if not six.PY3 else kwargs['login']
                func_cls._user = cls._get_github_user(login, kwargs['ui'])
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
