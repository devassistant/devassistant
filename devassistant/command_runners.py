import copy
import functools
import getpass
import logging
import os
import re

import jinja2
import progress.bar
import six
import yaml

import devassistant

from devassistant import exceptions
from devassistant.remote_auth import GitHubAuth
from devassistant.command_helpers import ClHelper, DialogHelper
from devassistant import lang
from devassistant.logger import logger
from devassistant.package_managers import DependencyInstaller
from devassistant import settings
from devassistant import utils
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
            assistant should rather return [False, 'something'] then raise exception, so that
            execution could continue.

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
        if c.input_res and not isinstance(c.input_res, dict):
            raise exceptions.CommandException('{0} needs a mapping as input!'.format(c.comm_type))
        if c.comm_type == 'ask_password':
            res = DialogHelper.ask_for_password(**c.input_res)
        elif c.comm_type == 'ask_confirm':
            res = DialogHelper.ask_for_confirm_with_message(**c.input_res)
        else:
            raise exceptions.CommandException('Unknown command type {ct}.'.format(ct=c.comm_type))
        return bool(res), res


@register_command_runner
class CallCommandRunner(CommandRunner):
    @classmethod
    def matches(cls, c):
        return c.comm_type == 'call' or c.comm_type == 'use'

    @classmethod
    def run(cls, c):
        sect_type = c.kwargs['__section__']
        assistant = c.kwargs['__assistant__']
        section, sourcefile = cls.get_section_from_call(c.input_res, sect_type, assistant)
        if not section:
            msg = 'Couldn\'t find {t} section "{n}".'.format(t=c.kwargs['__section__'],
                                                             n=c.input_res)
            raise exceptions.CommandException(msg)

        if cls.is_snippet_call(c.input_res):
            # we're calling a snippet => add files and files_dir to kwargs
            snippet = yaml_snippet_loader.YamlSnippetLoader.\
                get_snippet_by_name(c.input_res.split('.')[0])

            c.kwargs['__files__'].append(snippet.get_files_section())
            c.kwargs['__files_dir__'].append(snippet.get_files_dir())
            c.kwargs['__sourcefiles__'].append(snippet.path)

        if sect_type == 'dependencies':
            result = lang.dependencies_section(section, copy.deepcopy(c.kwargs), runner=assistant)
        else:
            result = lang.run_section(section,
                                      copy.deepcopy(c.kwargs),
                                      runner=assistant)

        if cls.is_snippet_call(c.input_res):
            c.kwargs['__files__'].pop()
            c.kwargs['__files_dir__'].pop()
            c.kwargs['__sourcefiles__'].pop()

        return result

    @classmethod
    def is_snippet_call(cls, cmd_call):
        return not ((cmd_call == 'self' or cmd_call.startswith('self.')) or
                    (cmd_call == 'super' or cmd_call.startswith('super.')))

    @classmethod
    def get_section_from_call(cls, cmd_call, section_type, assistant):
        """Returns a section and source file from call command.

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
            sourcefile, None if not found
        """
        section = None
        call_parts = cmd_call.split('.')
        section_name = call_parts[1] if len(call_parts) > 1 else section_type

        section = sourcefile = None

        if call_parts[0] == 'self':
            section = getattr(assistant, '_' + section_name, None)
            sourcefile = assistant.path
        elif call_parts[0] == 'super':
            a = assistant.superassistant
            while a:
                if hasattr(a, 'assert_fully_loaded'):
                    a.assert_fully_loaded()
                if hasattr(a, '_' + section_name):
                    section = getattr(a, '_' + section_name)
                    sourcefile = a.path
                    break
                a = a.superassistant
        else:  # snippet
            try:
                snippet = yaml_snippet_loader.YamlSnippetLoader.get_snippet_by_name(call_parts[0])
                if section_type == 'run':
                    section = snippet.get_run_section(section_name) if snippet else None
                else:
                    section = snippet.get_dependencies_section(section_name) if snippet else None
                sourcefile = snippet.path
            except exceptions.SnippetNotFoundException:
                pass  # snippet not found => leave section = sourcefile = None

        return section, sourcefile


@register_command_runner
class ClCommandRunner(CommandRunner):
    @classmethod
    def matches(cls, c):
        return c.comm_type.startswith('cl')

    @classmethod
    def run(cls, c):
        log_level = logging.DEBUG
        if 'i' in c.comm_type:
            log_level = logging.INFO
        scls = []
        if '__scls__' in c.kwargs:
            scls = functools.reduce(lambda x, y: x + y, c.kwargs['__scls__'], scls)
        # if there is an exception, just let it bubble up
        result = ClHelper.run_command(c.input_res, log_level, scls=scls)

        return [True, result]


@register_command_runner
class DependenciesCommandRunner(CommandRunner):
    @classmethod
    def matches(cls, c):
        return c.comm_type.startswith('dependencies')

    @classmethod
    def run(cls, c):
        if not isinstance(c.input_res, list):
            msg = 'Dependencies for installation must be list, got {v}.'.format(v=c.input_res)
            raise exceptions.CommandException(msg)

        di = DependencyInstaller()
        di.install(c.input_res)
        return [True, c.input_res]


@register_command_runner
class DotDevassistantCommandRunner(CommandRunner):
    @classmethod
    def matches(cls, c):
        return c.comm_type.startswith('dda_')

    @classmethod
    def run(cls, c):
        cls.check_args(c)
        if c.comm_type == 'dda_c':
            cls._dot_devassistant_create(c.input_res, c.kwargs)
        elif c.comm_type == 'dda_r':
            cls._dot_devassistant_read(c.input_res, c.kwargs)
        elif c.comm_type == 'dda_dependencies':
            cls._dot_devassistant_dependencies(c.input_res, c.kwargs)
        elif c.comm_type == 'dda_run':
            cls._dot_devassistant_run(c.input_res, c.kwargs)
        elif c.comm_type == 'dda_w':
            cls._dot_devassistant_write(c.input_res)
        else:
            raise exceptions.CommandException('Unknown command type {ct}.'.format(ct=c.comm_type))

        return [True, '']

    @classmethod
    def check_args(cls, c):
        if c.comm_type == 'dda_w':
            if not isinstance(c.input_res, list) or len(c.input_res) != 2:
                msg = 'dda_w expects Yaml list with path to .devassistant and mapping to write.'
                raise exceptions.CommandException(msg)
        else:
            if not isinstance(c.input_res, six.string_types):
                msg = '{0} expects a string as an argument.'.format(c.comm_type)
                raise exceptions.CommandException(msg)

    @classmethod
    def __dot_devassistant_write_struct(cls, directory, struct):
        """Helper for other methods that write to .devassistant file."""
        dda_path = os.path.join(os.path.abspath(os.path.expanduser(directory)), '.devassistant')
        f = open(dda_path, 'w')
        yaml.dump(struct, stream=f, default_flow_style=False)
        f.close()

    @classmethod
    def __dot_devassistant_read_exact(cls, directory):
        """Helper for other methods that read .devassistant file."""
        dda_path = os.path.join(os.path.abspath(os.path.expanduser(directory)), '.devassistant')
        try:
            with open(dda_path, 'r') as stream:
                return yaml.load(stream)
        except IOError as e:
            msg = 'Couldn\'t find/open/read .devassistant file: {0}'.format(e)
            raise exceptions.CommandException(msg)

    @classmethod
    def _dot_devassistant_create(cls, directory, kwargs):
        # we will only write original cli/gui args, other kwargs are "private" for this run
        original_kwargs = {}
        arg_names = map(lambda arg: arg.name, kwargs['__assistant__'].args)
        for arg in arg_names:
            if arg in kwargs:  # only write those that were actually used on invocation
                original_kwargs[arg] = kwargs[arg]
        to_write = {'devassistant_version': devassistant.__version__,
                    'original_kwargs': original_kwargs,
                    'dependencies': kwargs['__assistant__'].\
                        dependencies(kwargs=copy.deepcopy(original_kwargs), expand_only=True)}
        cls.__dot_devassistant_write_struct(directory, to_write)

    @classmethod
    def _dot_devassistant_read(cls, comm, kwargs):
        """Reads and stores data from .devassistant file in kwargs.
        On top of it, it adds:
        - "name" - contains the name of current directory.
        - "dda__<var>" - (yes, that is double underscore) - for each <var> that
          this project was created with.
        """
        result = cls.__dot_devassistant_read_exact(comm)

        for k, v in result.items():
            kwargs.setdefault(k, v)
        for k, v in result.get('original_kwargs', {}).items():
            kwargs.setdefault('dda__' + k, v)
        kwargs.setdefault('name', os.path.basename(os.path.abspath(os.path.expanduser(comm))))

    @classmethod
    def _dot_devassistant_dependencies(cls, comm, kwargs):
        struct = []
        dda_content = cls.__dot_devassistant_read_exact(comm)
        original_kwargs = dda_content.get('original_kwargs', {})
        mixed_kwargs = copy.deepcopy(original_kwargs)
        mixed_kwargs.update(kwargs)
        struct = lang.dependencies_section(dda_content.get('dependencies', []),
                                           mixed_kwargs,
                                           runner=kwargs.get('__assistant__'))
        lang.Command('dependencies', struct, mixed_kwargs).run()

    @classmethod
    def _dot_devassistant_run(cls, comm, kwargs):
        dda_content = cls.__dot_devassistant_read_exact(comm)
        # TODO: we should really create devassistant.util.expand_path to not use
        # abspath + expanduser everywhere all the time...
        dda_fullpath = os.path.join(os.path.abspath(os.path.expanduser(comm)), '.devassistant')
        kwargs.setdefault('__sourcefiles__', [])
        kwargs['__sourcefiles__'].append(dda_fullpath)
        lang.run_section(dda_content.get('run', []),
                         kwargs,
                         runner=kwargs.get('__assistant__'))
        kwargs['__sourcefiles__'].pop()

    @classmethod
    def _dot_devassistant_write(cls, comm):
        dda_content = cls.__dot_devassistant_read_exact(comm[0])
        dda_content.update(comm[1])
        cls.__dot_devassistant_write_struct(comm[0], dda_content)


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
        args = c.input_res
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
            kwargs[k] = getattr(cls, '_guess_' + k)(args_rest.get(k), c.kwargs)

        return comm, kwargs

    @classmethod
    def _guess_login(cls, explicit, ctxt):
        """Get github login, either from explicitly given string or 'github' global variable
        or from local username.

        Args:
            ctxt: global context

        Returns:
            guessed github login
        """
        return explicit or ctxt.get('github', None) or getpass.getuser()

    @classmethod
    def _guess_reponame(cls, explicit, ctxt):
        """Extract reponame, either from explicitly given string or from 'name' global variable,
        which is possibly a path.

        Args:
            ctxt: global context

        Returns:
            guessed reponame
        """
        name = explicit or ctxt.get('name')
        if not name:
            raise exceptions.CommandException('Cannot guess Github reponame - no argument given'
                                              'and there is no "name" variable.')
        return name

    @classmethod
    def _guess_repo_url(cls, explicit, ctxt):
        """Get repo to fork in form of '<login>/<reponame>' from explicitly given string or
        global variable 'url'.

        Args:
            ctxt: global context

        Returns:
            guessed fork reponame
        """
        url = explicit or ctxt.get('url')
        if not url:
            raise exceptions.CommandException('Cannot guess name of Github repo to fork - no'
                                              'argument given and there is no "url" variable.')

        url = url[:-4] if url.endswith('.git') else url
        # if using git@github:username/reponame.git, strip the stuff before ":"
        url = url.split(':')[-1]
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
        ClHelper.run_command("git remote add origin git@github.com{dl}:{l}/{r}.git".\
                             format(dl=dash_login, l=login, r=reponame),
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
        logger.info('Forking {repo} for user {login} on Github ...'.\
            format(login=kwargs['login'], repo=kwargs['repo_url']))
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
        if c.comm_type in map(lambda x: 'log_{0}'.format(x), settings.LOG_LEVELS_MAP):
            logger.log(logging._levelNames[settings.LOG_LEVELS_MAP[c.comm_type[-1]]], c.input_res)
            if c.comm_type[-1] in 'ce':
                e = exceptions.CommandException(c.input_res)
                e.already_logged = True
                raise e
        else:
            raise exceptions.CommandException('Unknown command type {ct}.'.format(ct=c.comm_type))

        return [True, c.input_res]


@register_command_runner
class SCLCommandRunner(CommandRunner):
    @classmethod
    def matches(cls, c):
        return c.comm_type.startswith('scl ')

    @classmethod
    def run(cls, c):
        c.kwargs.setdefault('__scls__', [])
        c.kwargs.setdefault('__assistant__', None)
        c.kwargs['__scls__'].append(c.comm_type.split()[1:])
        # use "c.comm", not "c.input_res" - we need unformatted input here
        retval = lang.run_section(c.comm,
                                  c.kwargs,
                                  runner=c.kwargs['__assistant__'])
        c.kwargs['__scls__'].pop()

        return retval


@register_command_runner
class Jinja2Runner(CommandRunner):
    @classmethod
    def matches(cls, c):
        return c.comm_type == 'jinja_render'

    @classmethod
    def _make_output_file_name(cls, args, template):
        """ Form an output filename:
            - if 'output' is specified among `args`, just use it!
            - otherwise, output file name produced from the source template name
              by stripping '.tpl' suffix if latter presents, or just used as
              if none given.
        """
        output = ''
        if 'output' in args:
            assert(isinstance(args['output'], six.string_types))
            output = args['output']
        elif template.endswith('.tpl'):
            output = template[:-len('.tpl')]
        else:
            output = template

        # Form a destination file
        result_filename = os.path.join(args['destination'], output)
        return result_filename

    @classmethod
    def _try_obtain_mandatory_params(cls, args):
        """ Retrieve required parameters from `args` dict:
         - 'template'    template descriptor from `files' section. it consist of
                         the only `source' key -- a name of template to use
         - 'data'        dict of parameters to use when rendering
         - 'destination' path for output files
        """

        if 'template' not in args or not isinstance(args['template'], dict):
            raise exceptions.CommandException('Missed template parameter or wrong type')
        template = args['template']

        if 'source' not in template or not isinstance(template['source'], six.string_types):
            raise exceptions.CommandException('Missed template parameter or wrong type')
        template = template['source']

        if 'destination' not in args or not isinstance(args['destination'], six.string_types):
            raise exceptions.CommandException('Missed destination parameter or wrong type')

        if not os.path.isdir(args['destination']):
            raise exceptions.CommandException("Destination directory doesn't exists")

        data = {}
        if 'data' in args and isinstance(args['data'], dict):
            data = args['data']
        logger.debug('Template context data: {0}'.format(data))

        return (template, cls._make_output_file_name(args, template), data)

    @classmethod
    def run(cls, c):
        # Transform list of dicts (where keys are unique) into a single dict
        args = c.input_res
        logger.debug('args={0}'.format(repr(args)))

        # Get parameters
        template, result_filename, data = cls._try_obtain_mandatory_params(args)

        # Create an environment!
        logger.debug('Using templats dir: {0}'.format(c.files_dir))
        env = jinja2.Environment(loader=jinja2.FileSystemLoader(c.files_dir))
        env.trim_blocks = True
        env.lstrip_blocks = True

        # Get a template instance
        tpl = None
        try:
            logger.debug('Using template file: {0}'.format(template))
            tpl = env.get_template(template)
        except jinja2.TemplateNotFound as e:
            raise exceptions.CommandException('Template {t} not found in path {p}.'.\
                    format(t=template, p=c.files_dir))
        except jinja2.TemplateError as e:
            raise exceptions.CommandException('Template file failure: {0}'.format(e.message))

        # Check if destination file exists, overwrite if needed
        if os.path.exists(result_filename):
            overwrite = args['overwrite'] if 'overwrite' in args else False
            overwrite = True if overwrite in ['True', 'true', 'yes'] else False
            if overwrite:
                logger.info('Overwriting the destination file {0}'.format(result_filename))
                os.remove(result_filename)
            else:
                raise exceptions.CommandException('The destination file already exists: {0}'.\
                    format(result_filename))

        # Generate an output file finally...
        with open(result_filename, 'w') as out:
            result = tpl.render(**data)
            out.write(result)

        return (True, 'success')


@register_command_runner
class SuCommandRunner(CommandRunner):
    @classmethod
    def matches(cls, c):
        return c.comm_type == 'su' or c.comm_type.startswith('su ')

    @classmethod
    def get_user_from_comm_type(cls, comm_type):
        user = None
        split_type = comm_type.split()
        if len(split_type) == 1:
            pass  # no-op
        elif len(split_type) != 3 or split_type[1] != '-':
            raise exceptions.CommandExceptions('"su" expects format "su[ - username]".')
        else:
            user = split_type[2]
        return user

    @classmethod
    def run(cls, c):
        user = cls.get_user_from_comm_type(c.comm_type)
        to_run = utils.cl_string_for_da_eval(c.comm, c.kwargs)
        pkexec_to_run = ['pkexec']
        if user:
            pkexec_to_run.extend(['--user', user])
        pkexec_to_run.append(to_run)
        pkexec_to_run = ' '.join(pkexec_to_run)

        def sub_da_logger(msg):
            logger.info(msg, extra={'event_type': 'sub_da'})

        try:
            out = ClHelper.run_command(pkexec_to_run, output_callback=sub_da_logger)
            ret = True
        except exceptions.ClException as e:
            out = e.output
            ret = False
        return [ret, out]


@register_command_runner
class DockerCommandRunner(object):
    try:
        _docker_module = utils.import_module('docker')
    except:
        _docker_module = None
    _client = None

    @classmethod
    def matches(cls, c):
        return c.comm_type.startswith('docker_')

    @classmethod
    def get_client(cls, timeout=None):
        if not cls._client:
            cls._client = cls._docker_module.Client(timeout=timeout)
        return cls._client

    @classmethod
    def run(cls, c):
        # TODO: decide the format of return values and return according to that in all cases
        if not cls._docker_module:
            logger.warning('docker-py not installed, cannot execute docker command.')
            return [False, '']

        if c.comm_type == 'docker_b':
            # TODO: allow providing another argument - a repository name/tag for the built image
            return cls._docker_build(c.input_res)
        else:
            raise exceptions.CommandException('Unknown command type {ct}.'.format(ct=c.comm_type))

    @classmethod
    def _docker_build(cls, directory):
        logger.info('Building Docker image ...')
        client = cls.get_client()
        stream = client.build(path=directory, rm=True, stream=True)

        # If there are more images downloaded in paralel, the generator
        # displays and redisplays their progress bars in random order, not telling us
        # which progress line it's printing now.
        # So we rather remember these by download sizes (hopefully different)
        # and create one common progress bar for all images combined.
        # Progress is measured by number of "=" + one ">" in the bar

        downloads = {}  # maps size of image to percent downloaded
        downloads_re = re.compile(r'(\[[=> ]+\]).+/([\.0-9]* .B)')
        pgb = progress.bar.Bar('Downloading Images', fill='=', suffix='%(percent)d %%')

        # 'Pulling repository' isn't excluded intentionally
        exclude_patterns = ['Download complete', 'Pulling image', 'Pulling dependent layers',
                            'Pulling metadata', 'Pulling fs layer']

        success = False
        success_re = re.compile(r'Successfully built ([0-9a-f]+)')
        final_image = ''

        for line in stream:
            line = line.strip()
            download_match = downloads_re.search(line)

            # either progress the progress bar or print the line
            if download_match:
                percent = float(download_match.group(1).count('=') + 1) / \
                    (len(download_match.group(1)) - 2) * 100
                downloads[download_match.group(2)] = percent
                pgb.goto(sum(list(downloads.values())) / len(downloads))
                if percent >= 100:
                    pgb.finish()
            else:
                # Filter unwanted docker output
                if not filter(line.startswith, exclude_patterns):
                    logger.info(line.strip())

            # the success line doesn't necesarilly have to be at the very end of output...
            success_found = success_re.search(line)
            if success_found:
                success = True
                final_image = success_found.group(1)

        pgb.finish()
        if success:
            logger.info('Finished building Docker image.')
        else:
            logger.info('Failed to build Docker image.')
        return success, final_image
