import copy
import functools
import getpass
import logging
import os

import yaml

from devassistant import exceptions
from devassistant import command
from devassistant.command_helpers import ClHelper, DialogHelper
from devassistant import lang
from devassistant.logger import logger
from devassistant.package_managers import DependencyInstaller
from devassistant import settings
from devassistant import utils
from devassistant import version
from devassistant import yaml_snippet_loader

command_runners = []

def register_command_runner(command_runner):
    command_runners.append(command_runner)
    return command_runner

class CommandRunner(object):
    @classmethod
    def matches(cls, c):
        """Returns True if this command runner can run given command,
        False otherwise.

        Args:
            c - command to check, instance of devassistant.command.Command

        Returns:
            True if this runner can run the command, False otherwise
        """
        raise NotImplementedError()

    @classmethod
    def run(cls, c):
        """Runs the given command.

        Args:
            c - command to run, instance of devassistant.command.Command

        Returns:
            Tuple/list [logical_result, result] of the run (e.g. [True, 'output']). Usually,
            assistant should rather raise an exception than return [False, 'something'].

        Raises:
            Any exception that's subclass of devassistant.exceptions.CommandException
        """
        raise NotImplementedError()

@register_command_runner
class AskCommandRunner(CommandRunner):
    @classmethod
    def matches(cls, c):
        return c.comm_type.startswith('ask_')

    @classmethod
    def run(cls, c):
        var, args = cls.format_args(c)
        if c.comm_type == 'ask_password':
            result = [True, DialogHelper.ask_for_password(**args)]
        elif c.comm_type == 'ask_confirm':
            result = [True, DialogHelper.ask_for_confirm_with_message(**args)]
        else:
            raise exceptions.CommandException('Unknown command type {ct}.'.format(ct=c.comm_type))
        c.kwargs[var] = result[1]
        return result

    @classmethod
    def format_args(cls, c):
        # get variable name before formatting
        var = lang.get_var_name(c.comm[0])
        fmtd = c.format_deep()
        return var, fmtd[1]

@register_command_runner
class CallCommandRunner(CommandRunner):
    @classmethod
    def matches(cls, c):
        return c.comm_type == 'call' or c.comm_type == 'use'

    @classmethod
    def run(cls, c):
        sect_type = c.kwargs['__section__']
        assistant = c.kwargs['__assistant__']
        section = cls.get_section_from_call(c.comm, sect_type, assistant)
        if not section:
            msg = 'Couldn\'t find {t} section "{n}".'.format(t=c.kwargs['__section__'],
                                                             n=c.comm)
            raise exceptions.CommandException(msg)

        if cls.is_snippet_call(c.comm):
            # we're calling a snippet => add files and files_dir to kwargs
            snippet = yaml_snippet_loader.YamlSnippetLoader.get_snippet_by_name(c.comm.split('.')[0])

            c.kwargs['__files__'].append(snippet.get_files_section())
            c.kwargs['__files_dir__'].append(snippet.get_files_dir())

        if sect_type == 'dependencies':
            result = lang.dependencies_section(section, copy.deepcopy(c.kwargs), runner=assistant)
        else:
            result = lang.run_section(section, copy.deepcopy(c.kwargs), runner=assistant)

        if cls.is_snippet_call(c.comm):
            c.kwargs['__files__'].pop()
            c.kwargs['__files_dir__'].pop()

        return result

    @classmethod
    def is_snippet_call(cls, cmd_call):
        return not ((cmd_call == 'self' or cmd_call.startswith('self.')) or
                    (cmd_call == 'super' or cmd_call.startswith('super.')))

    @classmethod
    def get_section_from_call(cls, cmd_call, section_type, assistant):
        """Returns a section from call command.

        Examples:
        - self.dependencies_bar ~> dependencies_bar section from this assistant
        - eclipse.run_foo ~> run_foo section from eclipse snippet
        - super.dependencies ~> dependencies section from first superassistant that has such

        If the part after dot is omitted, "section_type" is used instead

        Args:
            cmd_call - a string with the call, e.g. "eclipse.run_python"
            section_type - either "dependencies" or "run"
            assistant - current assistant for the possibility of trying to use "self" or "super"

        Returns:
            section to call (list), None if not found
        """
        section = None
        call_parts = cmd_call.split('.')
        section_name = call_parts[1] if len(call_parts) > 1 else section_type

        if call_parts[0] == 'self':
            section = getattr(assistant, '_' + section_name, None)
        elif call_parts[0] == 'super':
            a = assistant.superassistant
            while a:
                if hasattr(a, 'assert_fully_loaded'):
                    a.assert_fully_loaded()
                if hasattr(a, '_' + section_name):
                    section = getattr(a, '_' + section_name)
                    break
        else: # snippet
            try:
                snippet = yaml_snippet_loader.YamlSnippetLoader.get_snippet_by_name(call_parts[0])
                if section_type == 'run':
                    section = snippet.get_run_section(section_name) if snippet else None
                else:
                    section = snippet.get_dependencies_section(section_name) if snippet else None
            except exceptions.SnippetNotFoundException:
                section = None

        return section

@register_command_runner
class ClCommandRunner(CommandRunner):
    @classmethod
    def matches(cls, c):
        return c.comm_type.startswith('cl')

    @classmethod
    def run(cls, c):
        comm = c.format_str()
        log_level = logging.DEBUG
        if 'i' in c.comm_type:
            log_level = logging.INFO
        scls = []
        if '__scls__' in c.kwargs:
            scls = functools.reduce(lambda x, y: x + y, c.kwargs['__scls__'], scls)
        # if there is an exception, just let it bubble up
        result = ClHelper.run_command(comm, log_level, scls=scls)

        return [True, result]

@register_command_runner
class DependenciesCommandRunner(CommandRunner):
    @classmethod
    def matches(cls, c):
        return c.comm_type.startswith('dependencies')

    @classmethod
    def run(cls, c):
        struct = c.format_deep()
        if not isinstance(struct, list):
            msg = 'Dependencies for installation must be list, got {v}.'.format(v=struct)
            raise exceptions.CommandException(msg)

        di = DependencyInstaller()
        di.install(struct)
        return [True, struct]

@register_command_runner
class DotDevassistantCommandRunner(CommandRunner):
    @classmethod
    def matches(cls, c):
        return c.comm_type.startswith('dda_')

    @classmethod
    def run(cls, c):
        comm = c.format_str()
        if c.comm_type == 'dda_c':
            cls._dot_devassistant_create(comm, c.kwargs)
        elif c.comm_type == 'dda_r':
            cls._dot_devassistant_read(comm, c.kwargs)
        elif c.comm_type == 'dda_dependencies':
            cls._dot_devassistant_dependencies(comm, c.kwargs)
        elif c.comm_type == 'dda_run':
            cls._dot_devassistant_run(comm, c.kwargs)
        else:
            raise exceptions.CommandException('Unknown command type {ct}.'.format(ct=c.comm_type))

        return [True, '']

    @classmethod
    def _dot_devassistant_create(cls, directory, kwargs):
        cls._dot_devassistant_path = os.path.join(directory, '.devassistant')
        f = open(cls._dot_devassistant_path, 'w')
        # write path to this subassistant
        path = []
        i = 0
        while settings.SUBASSISTANT_N_STRING.format(i) in kwargs:
            path.append(kwargs[settings.SUBASSISTANT_N_STRING.format(i)])
            # delete the dict member so that we don't write it out with other kwargs again
            del kwargs[settings.SUBASSISTANT_N_STRING.format(i)]
            i += 1

        if path and path[0] in settings.ASSISTANT_ROLES:
            path = path[1:]

        # we will only write original cli/gui args, other kwargs are "private" for this run
        original_kwargs = {}
        arg_names = map(lambda arg: arg.name, kwargs['__assistant__'].args)
        for arg in arg_names:
            if arg in kwargs: # only write those that were actually used on invocation
                original_kwargs[arg] = kwargs[arg]
        to_write = {'devassistant_version': version.VERSION,
                    'subassistant_path': path,
                    'original_kwargs': original_kwargs}
        yaml.dump(to_write, stream=f, default_flow_style=False)
        f.close()

    @classmethod
    def _dot_devassistant_read(cls, comm, kwargs):
        """Reads and stores data from .devassistant file in kwargs.
        On top of it, it adds:
        - "name" - contains the name of current directory.
        - "dda__<var>" - (yes, that is double underscore) - for each <var> that
          this project was created with.
        """
        dot_devassistant = os.path.join(os.path.abspath(os.path.expanduser(comm)), '.devassistant')
        try:
            with open(dot_devassistant, 'r') as stream:
                result = yaml.load(stream)
        except IOError as e:
            msg = 'Couldn\'t find properly formatted .devassistant file: {0}'.format(e)
            raise exceptions.CommandException(msg)

        for k, v in result.items():
            kwargs.setdefault(k, v)
        for k, v in result.get('original_kwargs', {}).items():
            kwargs.setdefault('dda__' + k, v)
        kwargs.setdefault('name', os.path.basename(os.path.abspath(os.path.expanduser(comm))))

    @classmethod
    def _dot_devassistant_dependencies(cls, comm, kwargs):
        struct = []
        dda_content = cls._dot_devassistant_read(comm, kwargs)
        original_assistant_path = dda_content.get('subassistant_path', [])
        if original_assistant_path:
            # if we have an original path, try to get original assistant
            original_path_as_dict = {}
            for i, subas in enumerate(original_assistant_path):
                original_path_as_dict[settings.SUBASSISTANT_N_STRING.format(i)] = subas
            from devassistant.bin import CreatorAssistant
            from devassistant import yaml_assistant
            try:
                path = CreatorAssistant().get_selected_subassistant_path(**original_path_as_dict)
            except exceptions.AssistantNotFoundException as e:
                path = []
                logger.warning(str(e))
            for a in path:
                #TODO: maybe figure out more DRY code (similar is in path_runner, too)
                if 'dependencies' in vars(a.__class__) or \
                   isinstance(a, yaml_assistant.YamlAssistant):
                    struct.extend(a.dependencies(dda_content.get('original_kwargs', {})))
            struct.extend(lang.dependencies_section(dda_content.get('dependencies', []),
                                                    kwargs,
                                                    runner=kwargs['__assistant__']))
        command.Command('dependencies', struct, kwargs).run()

    @classmethod
    def _dot_devassistant_run(cls, comm, kwargs):
        dda_content = cls._dot_devassistant_read(comm, **kwargs)
        lang.run_section(dda_content.get('run', []), kwargs, runner=kwargs['__assistant__'])

class GitHubAuth(object):
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
                pass # token is not available yet

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
                # login with username/password
                password = DialogHelper.ask_for_password(
                        prompt='Github Password for {username}:'.format(username=login))
                gh = cls._gh_module.Github(login_or_token=login, password=password)
                cls._user = gh.get_user()
                try:
                    cls._user.login
                    cls._github_create_auth() # create auth for future use
                except cls._gh_module.GithubException as e:
                    msg = 'Wrong username or password\nGitHub exception: {0}'.format(e)
                    # reset cls._user to None, so that we don't use it if calling this multiple times
                    cls._user = None
                    raise exceptions.CommandException(msg)
        return cls._user

    @classmethod
    def _github_create_auth(cls):
        """ Store token into ~/.gitconfig.

        If token is not defined then store it into ~/.gitconfig file
        """
        if not cls._token:
            try:
                auth = cls._user.create_authorization(scopes=['repo', 'user'], note="DeveloperAssistant")
                ClHelper.run_command("git config --global github.token.{login} {token}".format(
                    login=cls._user.login,
                    token=auth.token))
                ClHelper.run_command("git config --global github.user.{login} {login}".format(
                    login=cls._user.login))
            except cls._gh_module.GithubException as e:
                logger.warning('Creating authorization failed: {0}'.format(e))

    @classmethod
    def _github_create_ssh_key(cls):
        try:
            login = cls._user.login
            pkey_path = '{home}/.ssh/{keyname}'.format(home=os.path.expanduser('~'),
                                                       keyname=settings.GITHUB_SSH_KEYNAME.format(login=login))
            # create ssh keys here
            if not os.path.isfile('{pkey_path}.pub'.format(pkey_path=pkey_path)):
                ClHelper.run_command('ssh-keygen -t rsa -f {pkey_path}\
                                     -N \"\" -C \"DeveloperAssistant\"'.\
                                     format(pkey_path=pkey_path))
                ClHelper.run_command('ssh-add {pkey_path}'.format(pkey_path=pkey_path))
            public_key = ClHelper.run_command('cat {pkey_path}.pub'.format(pkey_path=pkey_path))
            # find out if this key is already registered with this user
            for key in cls._user.get_keys():
                # don't use "==" because we have comments etc added in public_key
                if key._key in public_key:
                    break
            else:
                cls._user.create_key("devassistant", public_key)
            # next, create ~/.ssh/config entry for the key, if system username != GH login
            cls._github_create_ssh_config_entry()
        except exceptions.ClException:
            pass # TODO: determine and log the error

    @classmethod
    def _github_create_ssh_config_entry(cls):
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
            if needs_to_add_config_entry:
                fh = os.fdopen(os.open(ssh_config, os.O_WRONLY|os.O_CREAT|os.O_APPEND, 0o600), 'a')
                fh.write(settings.GITHUB_SSH_CONFIG.format(
                            login=cls._user.login,
                            keyname=settings.GITHUB_SSH_KEYNAME.format(login=cls._user.login)))
                fh.close()

    @classmethod
    def github_authenticated(cls, func):
        """Does user authentication, creates SSH keys if needed and injects "_user" attribute
        into class/object bound to the decorated function.
        Don't call any other methods of this class manually, this should be everything you need.
        """
        def inner(func_cls, *args, **kwargs):
            if not cls._gh_module:
                logger.warning('PyGithub not installed, skipping github authentication procedures.')
            elif not func_cls._user:
                # authenticate user, possibly also creating authentication for future use
                func_cls._user = cls._get_github_user(kwargs['login'])
                # create ssh key for pushing
                cls._github_create_ssh_key()
            return func(func_cls, *args, **kwargs)

        return inner

@register_command_runner
class GitHubCommandRunner(CommandRunner):
    _user = None
    try:
        _gh_module = utils.import_module('github')
    except:
        _gh_module = None
    _required_yaml_args = {'default': ['login', 'reponame'],
                           'create_fork': ['login', 'repo_url']}

    @classmethod
    def matches(cls, c):
        return c.comm_type == 'github'

    @classmethod
    def run(cls, c):
        """Arguments given to 'github' command may be:
        - Just a string (action), which implies that all the other arguments are deducted from
          global context and local system.
        - List containing a string (action) as a first item and rest of the args in a dict.
          (args not specified in the dict are taken from global context.

        Possible arguments:
        - login - taken from 'github' or system username - represents Github login
        - reponame - taken from 'name' (first applies os.path.basename) - repo to operate on
        """
        comm, kwargs = cls.format_args(c)
        if not cls._gh_module:
            logger.warning('PyGithub not installed, cannot execute github command.')
            return [False, '']

        # we pass arguments as kwargs, so that the auth decorator can easily query them
        # NOTE: these are not the variables from global context, but rather what
        # cls.format_args returned
        if comm == 'create_repo':
            ret = cls._github_create_repo(**kwargs)
        elif comm == 'push':
            ret = cls._github_push()
        elif comm == 'create_and_push':
            ret = cls._github_create_and_push(**kwargs)
        elif comm == 'add_remote_origin':
            ret = cls._github_add_remote_origin(**kwargs)
        elif comm == 'create_fork':
            ret = cls._github_fork(**kwargs)
        else:
            raise exceptions.CommandException('Unknown command type {ct}.'.format(ct=c.comm_type))

        return [True, ret or '']

    @classmethod
    def format_args(cls, c):
        args = c.format_deep()
        if isinstance(args, list):
            comm = args[0]
            args_rest = args[1]
        else:
            comm = args
            args_rest = {}
        # find out what arguments we will need
        kwargs = {}
        req_kwargs = cls._required_yaml_args.get(comm, cls._required_yaml_args['default'])
        for k in req_kwargs:
            kwargs[k] = getattr(cls, '_guess_' + k)(c.kwargs)
            if k in args_rest and not kwargs[k]:
                kwargs[k] = args_rest[k]

        return comm, kwargs

    @classmethod
    def _guess_login(cls, ctxt):
        """Get github login, either from 'github' global variable or from local username.

        Args:
            ctxt: global context

        Returns:
            guessed github login
        """
        return ctxt.get('github', None) or getpass.getuser()


    @classmethod
    def _guess_reponame(cls, ctxt):
        """Extracts reponame from 'name' global variable, which is possibly a path.

        Args:
            ctxt: global context

        Returns:
            guessed reponame
        """
        if not 'name' in ctxt:
            raise exceptions.CommandException('Cannot guess Github reponame - no argument given\
                                               and there is no "name" variable.')
        return os.path.basename(ctxt['name'])

    @classmethod
    def _guess_repo_url(cls, ctxt):
        """Get repo to fork in form of '<login>/<reponame>' from global variable 'url'.

        Args:
            ctxt: global context

        Returns:
            guessed fork reponame
        """
        if not 'url' in ctxt:
            raise exceptions.CommandException('Cannot guess name of Github repo to fork - no\
                                               argument given and there is no "url" variable.')

        url = ctxt['url'][:-4] if ctxt['url'].endswith('.git') else ctxt['url']
        return '/'.join(url.split('/')[-2:])

    @classmethod
    def _github_push(cls):
        ClHelper.run_command("git push -u origin master", logging.INFO)

    @classmethod
    def _github_remote_show_origin(cls):
        ClHelper.run_command("git remote show origin")

    @classmethod
    @GitHubAuth.github_authenticated
    def _github_add_remote_origin(cls, **kwargs):
        """Note: the kwargs are not the global context here, but what cls.format_args returns."""
        reponame = kwargs['reponame']
        login = kwargs['login']
        # if system username != GH login, we need to use git@github.com-{login}:...
        # else just git@github.com:...
        dash_login = ''
        if getpass.getuser() != login:
            dash_login = '-' + login
        ClHelper.run_command("git remote add origin git@github.com{dash_login}:{login}/{reponame}.git".\
                             format(dash_login=dash_login, login=login, reponame=reponame),
                             logging.INFO)

    @classmethod
    @GitHubAuth.github_authenticated
    def _github_create_repo(cls, **kwargs):
        """Create repo on GitHub.
        Note: the kwargs are not the global context here, but what cls.format_args returns.

        If repository already exists then CommandException will be raised.

        Raises:
            devassistant.exceptions.CommandException on error
        """
        reponame = kwargs['reponame']

        if reponame in map(lambda x: x.name, cls._user.get_repos()):
            msg = 'Repository already exists on GitHub'
            raise exceptions.CommandException(msg)
        else:
            try:
                new_repo = cls._user.create_repo(reponame)
            except cls._gh_module.GithubException:
                msg = 'Failed to create GitHub repo. This sometime happens when you delete '
                msg += 'a repo and then you want to create the same one immediately. Wait '
                msg += 'for few minutes and then try again.'
                raise exceptions.CommandException(msg)
            logger.info('Your new repository: {0}'.format(new_repo.html_url))

        return new_repo.clone_url

    @classmethod
    @GitHubAuth.github_authenticated
    def _github_add_remote_and_push(cls, **kwargs):
        """Add a remote and push to GitHub.
        Note: the kwargs are not the global context here, but what cls.format_args returns.

        Raises:
            devassistant.exceptions.CommandException on error
        """
        cls._github_add_remote_origin(**kwargs)
        cls._github_remote_show_origin()
        cls._github_push()

    @classmethod
    @GitHubAuth.github_authenticated
    def _github_create_and_push(cls, **kwargs):
        """Note: the kwargs are not the global context here, but what cls.format_args returns."""
        # we assume we're in the project directory
        logger.info('Registering your project on GitHub as {0}/{1}...'.\
                format(kwargs['login'],
                       kwargs['reponame']))
        cls._github_create_repo(**kwargs)
        logger.info('Pushing your project to the new GitHub repository...')
        cls._github_add_remote_and_push(**kwargs)
        logger.info('GitHub repository was created and source code pushed.')

    @classmethod
    @GitHubAuth.github_authenticated
    def _github_fork(cls, **kwargs):
        """Create a fork of repo from kwargs['fork_repo'].
        Note: the kwargs are not the global context here, but what cls.format_args returns.

        Raises:
            devassistant.exceptions.CommandException on error
        """
        fork_login, fork_reponame = kwargs['repo_url'].split('/')
        logger.info('Forking {repo} for user {login} on Github ...'.format(login=kwargs['login'],
                                                                           repo=kwargs['repo_url']))
        try:
            repo = cls._gh_module.Github().get_user(fork_login).get_repo(fork_reponame)
            fork = cls._user.create_fork(repo)
        except cls._gh_module.GithubException as e:
            msg = 'Failed to create Github fork with error: {err}'.format(err=e)
            raise exceptions.CommandException(msg)
        logger.info('Fork is ready at {url}.'.format(url=fork.html_url))
        return fork.clone_url

@register_command_runner
class LogCommandRunner(CommandRunner):
    @classmethod
    def matches(cls, c):
        return c.comm_type.startswith('log_')

    @classmethod
    def run(cls, c):
        comm = c.format_str()
        if c.comm_type in map(lambda x: 'log_{0}'.format(x), settings.LOG_LEVELS_MAP):
            logger.log(logging._levelNames[settings.LOG_LEVELS_MAP[c.comm_type[-1]]], comm)
            if c.comm_type[-1] in 'ce':
                e = exceptions.CommandException(comm)
                e.already_logged = True
                raise e
        else:
            raise exceptions.CommandException('Unknown command type {ct}.'.format(ct=c.comm_type))

        return [True, comm]