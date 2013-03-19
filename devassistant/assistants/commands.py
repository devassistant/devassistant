import getpass
import logging
import os

import github
import plumbum

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
        i = False
        if 'f' in comm_type:
            fg = True
        if 'i' in comm_type:
            i = True
        try:
            result = ClHelper.run_command(comm, fg, i)
        except plumbum.ProcessExecutionError as e:
            raise exceptions.RunException(e)

        return result.strip() if hasattr(result, 'strip') else result

class DotDevassistantCommand(object):
    @classmethod
    def matches(cls, comm_type):
        return comm_type.startswith('dda_')

    @classmethod
    def run(cls, comm_type, comm, **kwargs):
        if comm_type == 'dda_c':
            cls._dot_devassistant_create(comm, **kwargs)
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
        f.write('devassistant_version={0}'.format(version.VERSION))
        f.write('subassistant_path={0}'.format(' '.join(path)))
        f.close()

class GitHubCommand(object):
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
        username = cls._github_username(**kwargs)
        reponame = cls._github_reponame(**kwargs)
        password = getpass.getpass(prompt='GitHub password:', stream=None)

        gh = github.Github(username, password)
        user = gh.get_user()
        try:
            if reponame in map(lambda x: x.name, user.get_repos()):
                raise exceptions.RunException('Repository already exists on GiHub.')
            else:
                user.create_repo(reponame)
        except github.GithubException as e:
            raise exceptions.RunException('GitHub error: {0}'.format(e))

    @classmethod
    def _github_push(cls, **kwargs):
        """Add a remote and push to GitHub.

        Raises:
            devassistant.exceptions.RunException on error
        """
        username = cls._github_username(**kwargs)
        reponame = cls._github_reponame(**kwargs)
        has_remote = False

        try:
            result = ClHelper.run_command("git remote show origin")
            has_remote = True
        except plumbum.ProcessExecutionError as e:
            pass

        if not has_remote:
            try:
                ClHelper.run_command("git remote add origin https://github.com/{0}/{1}.git".format(username, reponame), True, True)
            except plumbum.ProcessExecutionError as e:
                pass # TODO: what exactly happens here?

        ClHelper.run_command("git push origin master", True, True)

    @classmethod
    def _github_create_and_push(cls, **kwargs):
        with plumbum.local.cwd(os.path.abspath(os.path.expanduser(kwargs['name']))):
            ClHelper.run_command('cd {0}'.format(os.path.abspath(os.path.expanduser(kwargs['name']))))
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
