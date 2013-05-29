import getpass
import logging
import os

import github
import yaml

from devassistant import exceptions
from devassistant.command_helpers import ClHelper
from devassistant.logger import logger
from devassistant import settings
from devassistant import version

class ClCommand(object):
    @classmethod
    def matches(cls, comm_type):
        return comm_type.startswith('cl')

    @classmethod
    def run(cls, comm_type, comm, **kwargs):
        fg = False
        log_level = logging.DEBUG
        log_error = True
        if 'f' in comm_type:
            fg = True
        if 'i' in comm_type:
            log_level = logging.INFO
        if 'n' in comm_type:
            log_error = False
        try:
            result = ClHelper.run_command(comm, fg, log_level)
        except exceptions.ClException as e:
            if log_error:
                logger.error(e)
            raise exceptions.RunException(e)

        return result.strip() if hasattr(result, 'strip') else result

class DotDevassistantCommand(object):
    @classmethod
    def matches(cls, comm_type):
        return comm_type.startswith('dda_')

    @classmethod
    def run(cls, comm_type, comm, **kwargs):
        if comm_type == 'dda_c':
            return cls._dot_devassistant_create(comm, **kwargs)
        elif comm_type == 'dda_r':
            return cls._dot_devassistant_read(comm, **kwargs)
        else:
            logger.warning('Unknown .devassistant command {0}, skipping.'.format(comm_type))

    @classmethod
    def _dot_devassistant_create(cls, directory, **kwargs):
        cls._dot_devassistant_path = os.path.join(directory, '.devassistant')
        f = open(cls._dot_devassistant_path, 'w')
        # write path to this subassistant
        path = []
        i = 0
        while settings.SUBASSISTANT_N_STRING.format(i) in kwargs:
            path.append(kwargs[settings.SUBASSISTANT_N_STRING.format(i)])
            i += 1
        to_write = {'devassistant_version': version.VERSION,
                    'subassistant_path': path}
        yaml.dump(to_write, stream=f, default_flow_style=False)
        f.close()

    @classmethod
    def _dot_devassistant_read(cls, comm, **kwargs):
        """Don't use this directly from assistants (yet), raises uncaught exception
        if anything goes wrong."""
        dot_devassistant = os.path.join(os.path.abspath(os.path.expanduser(comm)), '.devassistant')
        try:
            with open(dot_devassistant, 'r') as stream:
                result = yaml.load(stream)
        except IOError as e:
            msg = 'Couldn\'t find properly formatted .devassistant file: {0}'.format(e)
            logger.error(msg)
            raise exceptions.RunException(e)

        result['name'] = os.path.basename(os.path.abspath(os.path.expanduser(comm)))
        return result

class GitHubCommand(object):
    _token = ""
    _user = None

    @classmethod
    def matches(cls, comm_type):
        return comm_type == 'github'

    @classmethod
    def run(cls, comm_type, comm, **kwargs):
        if comm == 'create_repo':
            cls._github_create_repo(**kwargs)
        elif comm == 'push':
            cls._github_push(**kwargs)
        elif comm == 'create_and_push':
            cls._github_create_and_push(**kwargs)
        else:
            logger.warning('Unknow github command {0}, skipping.'.format(comm))

    @classmethod
    def _github_username(cls, **kwargs):
        # TODO: use git config github.user?
        return kwargs['github'] or getpass.getuser()

    @classmethod
    def _github_token(cls, **kwargs):
        if not cls._token:
            try:
                cls._token = ClHelper.run_command("git config github.token")
            except exceptions.ClException as e:
                # token is not available yet
                pass

        return cls._token

    @classmethod
    def _github_authorization(cls, **kwargs):
        """ Store token into ~/.gitconfig.

        If token is not defined then store them into ~/.gitconfig file

        """

        username = cls._github_username(**kwargs)
        if not cls._token:
            try:
                auth = cls._user.create_authorization(["repo"], "DeveloperAssistant")
                ClHelper.run_command("git config --global github.token {0}".format(auth.token))
                ClHelper.run_command("git config --global github.user {0}".format(username))
            except github.GithubException as e:
                msg = 'Creating authorization failed: {0}'.format(e)
                raise exceptions.RunException(msg)

    @classmethod
    def _github_reponame(cls, **kwargs):
        """Extracts reponame from name, which is possibly a path."""
        return os.path.basename(kwargs['name'])

    @classmethod
    def _get_gh_user(cls, username, token, **kwargs):
        if not cls._user:
            try:
                # try logging with token
                gh = github.Github(login_or_token=token)
                cls._user = gh.get_user()
                # try if the authentication was successful
                cls._user.name
            except github.GithubException:
                # login with username/password
                password = ClHelper.run_command("zenity --title=\"GitHub password\" --text \"Enter password:\" --entry --hide-text")
                gh = github.Github(login_or_token=username, password=password)
                cls._user = gh.get_user()
                cls._token = None
                try:
                    cls._user.name
                except github.GithubException as e:
                    msg = 'Wrong username or password\nGitHub exception: {0}'.format(e)
                    logger.error(msg)
                    # reset cls._user to None, so that we don't use it if calling this multiple times
                    cls._user = None
                    raise exceptions.RunException(msg)
        return cls._user

    @classmethod
    def _github_push_repo(cls, **kwargs):
        ClHelper.run_command("git push -u origin master", True, True)

    @classmethod
    def _github_remote_show_origin(cls, **kwargs):
        try:
            result = ClHelper.run_command("git remote show origin",)
        except exceptions.ClException as e:
            msg = 'Problem with getting remote content: {0}'.format(e)

    @classmethod
    def _github_add_remote_origin(cls, **kwargs):
        username = cls._github_username(**kwargs)
        reponame = cls._github_reponame(**kwargs)
        try:
            ClHelper.run_command("git remote add origin git@github.com:{0}/{1}.git".format(username, reponame), True, True)
        except exceptions.ClException as e:
            msg = "Command git remote add failed: {0}".format(e)
            raise exceptions.RunException(msg)

    @classmethod
    def _github_create_ssh_key(cls, **kwargs):
        try:
            # create ssh keys here
            if os.path.isfile("{0}/.ssh/dev_assistant_rsa.pub".format(os.path.expanduser('~'))) == False:
                ClHelper.run_command("ssh-keygen -t rsa -f {0}/.ssh/dev_assistant_rsa -N \"\" -C \"DeveloperAssistant\"".format(os.path.expanduser('~')))
            return ClHelper.run_command("cat {0}/.ssh/dev_assistant_rsa.pub".format(os.path.expanduser('~')))
        except exceptions.ClException as ep:
            pass

    @classmethod
    def _github_create_repo(cls, **kwargs):
        """Create repo on GitHub.

        If repository already exists then RunException will be raised.

        Raises:
            devassistant.exceptions.RunException on error
        """
        username = cls._github_username(**kwargs)
        reponame = cls._github_reponame(**kwargs)
        token = cls._github_token(**kwargs)
        gh_user = cls._get_gh_user(username, token, **kwargs)

        if reponame in map(lambda x: x.name, gh_user.get_repos()):
            msg = 'Repository already exists on GitHub'
            logger.error(msg)
            raise exceptions.RunException(msg)
        else:
            new_repo = cls._user.create_repo(reponame)
            logger.info('Your new repository: {0}'.format(new_repo.html_url))

    @classmethod
    def _github_push(cls, **kwargs):
        """Add a remote and push to GitHub.

        Raises:
            devassistant.exceptions.RunException on error
        """
        username = cls._github_username(**kwargs)
        reponame = cls._github_reponame(**kwargs)
        has_push = False
        cls._github_authorization(**kwargs)
        os.chdir(reponame)
        try:
            cls._github_remote_show_origin(**kwargs)
            cls._github_push_repo(**kwargs)
            has_push = True
        except exceptions.ClException as e:
            logger.info("Remote show origin failed")
            pass
        if not has_push:
            public_content = cls._github_create_ssh_key(**kwargs)
            try:
                cls._github_add_remote_origin(**kwargs)
                cls._github_push_repo(**kwargs)
            except exceptions.ClException as ep:
                pass
            except github.GithubException as e:
                msg = 'GitHub error: {0}'.format(e)
                logger.error(msg)
                raise exceptions.RunException(msg)

    @classmethod
    def _github_create_and_push(cls, **kwargs):
        # we assume we're in the project directory
        logger.info('Registering your project on GitHub as {0}/{1}...'.format(cls._github_username(**kwargs),
                                                                              cls._github_reponame(**kwargs)))
        cls._github_create_repo(**kwargs)
        logger.info('Pushing your project to the new GitHub repository...')
        cls._github_push(**kwargs)
        logger.info('GitHub repository was created and source code pushed.')


class LogCommand(object):
    @classmethod
    def matches(cls, comm_type):
        return comm_type.startswith('log_')

    @classmethod
    def run(cls, comm_type, comm, **kwargs):
        if comm_type in map(lambda x: 'log_{0}'.format(x), settings.LOG_LEVELS_MAP):
            logger.log(logging._levelNames[settings.LOG_LEVELS_MAP[comm_type[-1]]], comm)
            if comm_type[-1] in 'ce':
                raise exceptions.RunException(comm)
        else:
            logger.warning('Unknown logging command {0} with message {1}'.format(comm_type, comm))

commands = [ClCommand, DotDevassistantCommand, GitHubCommand, LogCommand]

def run_command(comm_type, comm, **kwargs):
    for c in commands:
        if c.matches(comm_type):
            return c.run(comm_type, comm, **kwargs)

    logger.warning('Unknown action type {0}, skipping.'.format(comm_type))
