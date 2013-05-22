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
        return kwargs['github'] or getpass.getuser()

    @classmethod
    def _github_reponame(cls, **kwargs):
        """Extracts reponame from name, which is possibly a path."""
        return os.path.basename(kwargs['name'])

    @classmethod
    def _github_create_repo(cls, **kwargs):
        """Create repo on GitHub.

        If repository already exists then RunException will be raised.

        Raises:
            devassistant.exceptions.RunException on error
        """
        has_token = False
        username = cls._github_username(**kwargs)
        reponame = cls._github_reponame(**kwargs)
        try:
            cls._token = ClHelper.run_command("git config github.token")
            has_token = True
        except exceptions.ClException as e:
            pass # TODO: what exactly happens here?
        if has_token:
            try:
                gh = github.Github(cls._token)
                user = gh.get_user()
            except github.GithubException as e:
                msg = 'GitHub token is not valid'
                has_token = False
                logger.error(msg)
                password = getpass.getpass(prompt='GitHub password:', stream=None)
                gh = github.Github(username, password)
        else:
            password = getpass.getpass(prompt='GitHub password:', stream=None)
            gh = github.Github(username, password)
        user = gh.get_user()
        try:
            if reponame in map(lambda x: x.name, user.get_repos()):
                msg = 'Repository already exists on GitHub'
                logger.error(msg)
                #raise exceptions.RunException(msg)
            else:
                if not has_token:
                    auth = user.create_authorization(["repo"],"Developer Assistant")
                    cls._token = auth.token
                    logger.info('Token is: {0}'.format(cls._token))
                    ClHelper.run_command("git config --global github.token {0}".format(cls._token))
                    ClHelper.run_command("git config --global github.user {0}".format(username))
                new_repo = user.create_repo(reponame)
                logger.info('Your new repository: {0}'.format(new_repo.html_url))
        except github.GithubException as e:
            msg = 'GitHub error: {0}'.format(e)
            logger.error(msg)
            raise exceptions.RunException(msg)

    @classmethod
    def _github_push(cls, **kwargs):
        """Add a remote and push to GitHub.

        Raises:
            devassistant.exceptions.RunException on error
        """
        username = cls._github_username(**kwargs)
        reponame = cls._github_reponame(**kwargs)
        has_remote = False
        has_push = False
        gh = github.Github(cls._token)
        os.chdir(reponame)
        try:
            result = ClHelper.run_command("git remote show origin")
            has_remote = True
        except exceptions.ClException as e:
            pass

        user = gh.get_user()
        if not has_push:
            # create ssh keys here
            rsa_key = "{0}/.ssh/dev_assistant_rsa".format(os.path.expanduser('~'))
            if os.path.isfile("{0}.pub".format(rsa_key)) == False:
                ClHelper.run_command("ssh-keygen -t rsa -f {0} -N \"\" -C \"DeveloperAssistant\"".format(rsa_key), True, True)
            public_content = ClHelper.run_command("cat {0}.pub".format(rsa_key))
        try:
            ClHelper.run_command("git remote add origin git@github.com:{0}/{1}.git".format(username, reponame), True, True)
            ClHelper.run_command("git push -u origin master", True, True)
            has_push = True
        except exceptions.ClException as ep:
            pass
        except github.GithubException as e:
            msg = 'GitHub error: {0}'.format(e)
            logger.error(msg)
        if not has_push:
            try:
                user.create_key(user.create_key("DeveloperAssistant", public_content))
            except github.GithubException as ge:
                pass
            try:
                user.create_key(user.create_key("DeveloperAssistant", public_content))
            except github.GithubException as ge:
                pass
            try:
                ClHelper.run_command("git remote rm origin", True, True)
                ClHelper.run_command("git remote add origin git@github.com:{0}/{1}.git".format(username, reponame), True, True)
                try:
                    ClHelper.run_command("git push -u origin master", True, True)
                    has_push = True
                except exceptions.ClException as ep:
                    pass
            except exceptions.ClException as e:
                pass # TODO: what exactly happens here?

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
