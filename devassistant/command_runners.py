import copy
import functools
import getpass
import grp
import logging
import os
import re
import time
import string
import sys

import jinja2
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
class UseCommandRunner(CommandRunner):
    @classmethod
    def matches(cls, c):
        return c.comm_type == 'use'

    @classmethod
    def is_snippet_call(cls, cmd_call):
        return not (cmd_call.startswith('self.') or cmd_call.startswith('super.'))

    @classmethod
    def run(cls, c):
        assistant = c.kwargs['__assistant__']
        kwargs = copy.deepcopy(c.kwargs)
        try:
            yaml_name, section_name = c.input_res.rsplit('.', 1)
        except ValueError:
            raise exceptions.CommandException('"use" command expects "use: what.which_section".')

        # Modify kwargs based on command
        if cls.is_snippet_call(c.input_res):
            snip = cls.get_snippet(yaml_name)
            section = cls.get_snippet_section(section_name, snip)

            kwargs['__files__'].append(snip.get_files_section())
            kwargs['__files_dir__'].append(snip.get_files_dir())
            kwargs['__sourcefiles__'].append(snip.path)
        else:
            assistant = cls.get_assistant(yaml_name, section_name, assistant)
            section = cls.get_assistant_section(section_name, assistant)

            kwargs['__assistant__'] = assistant

        # Get section with modified kwargs
        if section_name.startswith('dependencies'):
            result = lang.dependencies_section(section, kwargs, runner=assistant)
        else:
            result = lang.run_section(section, kwargs, runner=assistant)

        return result

    @classmethod
    def get_snippet(cls, yaml_name):
        try:
            return yaml_snippet_loader.YamlSnippetLoader.get_snippet_by_name(yaml_name)
        except exceptions.SnippetNotFoundException as e:
            raise exceptions.CommandException(e)

    @classmethod
    def get_snippet_section(cls, section_name, snip):
        if section_name.startswith('run'):
            section = snip.get_run_section(section_name) if snip else None
        else:
            section = snip.get_dependencies_section(section_name) if snip else None

        if not section:
            raise exceptions.CommandException('Couldn\'t find section "{t}" in snippet "{n}".'.\
                                              format(t=section_name, n=snip.dotted_name))
        return section

    @classmethod
    def get_assistant(cls, assistant_name, section_name, origin_assistant):
        if assistant_name == 'self':
            if not hasattr(origin_assistant, '_' + section_name):
                raise exceptions.CommandException('Assistant "{a}" has no section "{s}"'.\
                                                  format(a=origin_assistant.name,
                                                         s=section_name))
            return origin_assistant
        elif assistant_name == 'super':
            a = origin_assistant.superassistant
            while a:
                if hasattr(a, 'assert_fully_loaded'):
                    a.assert_fully_loaded()
                if hasattr(a, '_' + section_name):
                    return a
                a = a.superassistant
            raise exceptions.CommandException('No superassistant of {a} has section {s}'.\
                                              format(a=origin_assistant.name,
                                                     s=section_name))

    @classmethod
    def get_assistant_section(cls, section_name, assistant):
        if not hasattr(assistant, '_' + section_name):
            raise exceptions.CommandException('Assistant {a} has no section {s}'.\
                                                format(a=assistant.name,
                                                       s=section_name))
        return getattr(assistant, '_' + section_name)


@register_command_runner
class ClCommandRunner(CommandRunner):
    @classmethod
    def matches(cls, c):
        return c.comm_type.startswith('cl')

    @classmethod
    def run(cls, c):
        log_level = logging.DEBUG
        as_user = None
        if 'i' in c.comm_type:
            log_level = logging.INFO
        if 'r' in c.comm_type:
            as_user = 'root'
        # if there is an exception, just let it bubble up
        result = ClHelper.run_command(c.input_res, log_level, as_user=as_user)

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
                    'project_type': kwargs['__assistant__'].project_type,
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
                           'create_repo': ['login', 'reponame', 'private'],
                           'create_and_push': ['login', 'reponame', 'private'],
                           'create_fork': ['login', 'repo_url'],
                           'push': []}

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

        return ret

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
        name = explicit
        if not name:
            name = os.path.basename(ctxt.get('name', ''))
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
    def _guess_private(cls, explicit, ctxt):
        return bool(explicit or ctxt.get('github_private') or False)

    @classmethod
    def _github_push(cls):
        try:
            ret = ClHelper.run_command("git push -u origin master")
            logger.info('Source code was successfully pushed.')
            return (True, ret)
        except exceptions.ClException as e:
            logger.warning('Problem pushing source code: {0}'.format(e.output))
            return (False, e.output)

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
        try:
            logger.info('Adding Github repo as git remote ...')
            ret = ClHelper.run_command("git remote add origin git@github.com{dl}:{l}/{r}.git".\
                format(dl=dash_login, l=login, r=reponame))
            logger.info('Successfully added Github repo as git remote.')
            return (True, ret)
        except exceptions.ClException as e:
            logger.warning('Problem adding Github repo as git remote: {0}.'.format(e.output))
            return (False, e.output)

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
            msg = 'Failed to create Github repo: {0}/{1} alread exists.'.\
                format(cls._user.login, reponame)
            logger.warning(msg)
            return (False, msg)
        else:
            msg = ''
            success = False
            try:
                new_repo = cls._user.create_repo(reponame, private=kwargs['private'])
                msg = new_repo.clone_url
                success = True
            except cls._gh_module.GithubException as e:
                gh_errs = e.data.get('errors', [])
                gh_errs = '; '.join(map(lambda err: err.get('message', ''), gh_errs))
                msg = 'Failed to create GitHub repo. This sometime happens when you delete '
                msg += 'a repo and then you want to create the same one immediately. If that\'s '
                msg += 'the case, wait for few minutes and then try again.\n'
                msg += 'Github errors: ' + gh_errs
            except BaseException as e:
                msg = 'Failed to create Github repo: {0}'.\
                    format(getattr(e, 'message', 'Unknown error'))

            if success:
                logger.info('Your new repository: {0}'.format(new_repo.html_url))
            else:
                logger.warning(msg)

        return (success, msg)

    @classmethod
    @GitHubAuth.github_authenticated
    def _github_add_remote_and_push(cls, **kwargs):
        """Add a remote and push to GitHub. As this is not a callable subcommand of this
        command runner, it doesn't emit any informative logging messages on its own, only messages
        emitted by called methods.
        Note: the kwargs are not the global context here, but what cls.format_args returns.
        """
        ret = cls._github_add_remote_origin(**kwargs)
        if ret[0]:
            ret = cls._github_push()
        return ret

    @classmethod
    @GitHubAuth.github_authenticated
    def _github_create_and_push(cls, **kwargs):
        """Note: the kwargs are not the global context here, but what cls.format_args returns."""
        # we assume we're in the project directory
        logger.info('Registering your {priv}project on GitHub as {login}/{repo}...'.\
                format(priv='private ' if kwargs['private'] else '',
                       login=kwargs['login'],
                       repo=kwargs['reponame']))
        ret = cls._github_create_repo(**kwargs)
        if ret[0]:  # on success push the sources
            ret = cls._github_add_remote_and_push(**kwargs)
        return ret

    @classmethod
    @GitHubAuth.github_authenticated
    def _github_fork(cls, **kwargs):
        """Create a fork of repo from kwargs['fork_repo'].
        Note: the kwargs are not the global context here, but what cls.format_args returns.

        Raises:
            devassistant.exceptions.CommandException on error
        """
        timeout = 300 # 5 minutes
        fork_login, fork_reponame = kwargs['repo_url'].split('/')
        logger.info('Forking {repo} for user {login} on Github ...'.\
            format(login=kwargs['login'], repo=kwargs['repo_url']))
        success = False
        msg = ''
        try:
            repo = cls._gh_module.Github().get_user(fork_login).get_repo(fork_reponame)
            fork = cls._user.create_fork(repo)
            while timeout > 0:
                time.sleep(5)
                timeout -= 5
                try:
                    fork.get_contents('/') # This function doesn't throw an exception when clonable
                    success = True
                    break
                except cls._gh_module.GithubException as e:
                    if 'is empty' not in str(e):
                        raise e
            msg = fork.ssh_url
        except cls._gh_module.GithubException as e:
            msg = 'Failed to create Github fork with error: {err}'.format(err=e)
        except BaseException as e:
            msg = 'Exception while forking GH repo: {0}'.\
                format(getattr(e, 'message', 'Unknown error'))

        if success:
            logger.info('Fork is ready at {url}.'.format(url=fork.html_url))
        else:
            logger.warning(msg)

        return (success, msg)


@register_command_runner
class LogCommandRunner(CommandRunner):
    @classmethod
    def matches(cls, c):
        return c.comm_type.startswith('log_')

    @classmethod
    def run(cls, c):
        if c.comm_type in map(lambda x: 'log_{0}'.format(x), settings.LOG_LEVELS_MAP):
            logger.log(settings.LOG_SHORT_TO_NUM_LEVEL[c.comm_type[-1]], c.input_res)
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

        def scl_command_processor(cmd_str):
            if cmd_str.startswith('cd '):
                return cmd_str
            scls = []
            scls = functools.reduce(lambda x, y: x + y, c.kwargs['__scls__'], scls)
            cmd_str = 'scl {scls} - << DA_SCL_EOF\n {cmd_str} \nDA_SCL_EOF'.\
                format(cmd_str=cmd_str,
                       scls=' '.join(scls))
            return cmd_str

        ClHelper.command_processors['scl_command_processor'] = scl_command_processor

        # use "c.comm", not "c.input_res" - we need unformatted input here
        retval = lang.run_section(c.comm,
                                  c.kwargs,
                                  runner=c.kwargs['__assistant__'])

        ClHelper.command_processors.pop('scl_command_processor')
        return retval


@register_command_runner
class Jinja2Runner(CommandRunner):
    @classmethod
    def matches(cls, c):
        return c.comm_type in ['jinja_render', 'jinja_render_dir']

    @classmethod
    def _make_output_file_name(cls, outdir, template, output_override=None):
        """ Form an output filename by joining outdir and filename:
            - if 'output_override' is not empty string or None, just use it for filename
            - otherwise, use filename produced according to these rulse:
              - if template has '.tpl' suffix, strip it and use the stripped name
              - else just use given template name
        """

        output = ''
        if output_override:
            output = output_override
        elif template.endswith('.tpl'):
            output = template[:-len('.tpl')]
        else:
            output = template

        return os.path.join(outdir, output)

    @classmethod
    def _try_obtain_common_params(cls, comm):
        """ Retrieve parameters common for all jinja_render* actions from Command instance.
        These are mandatory:
        - 'template'    template descriptor from `files' section. it consist of
                         the only `source' key -- a name of template to use
        - 'data'        dict of parameters to use when rendering
        - 'destination' path for output files
        These are optional:
        - 'overwrite'   overwrite file(s) if it (they) exist(s)
        """
        args = comm.input_res
        ct = comm.comm_type

        wrong_tpl_msg = '{0} requires a "template" argument which must point to a file'.format(ct)
        wrong_tpl_msg += ' in "files" section. Got: {0}'.format(args.get('template', None))

        if 'template' not in args or not isinstance(args['template'], dict):
            raise exceptions.CommandException(wrong_tpl_msg)
        template = args['template']

        if 'source' not in template or not isinstance(template['source'], six.string_types):
            raise exceptions.CommandException(wrong_tpl_msg)
        template = template['source']

        if 'destination' not in args or not isinstance(args['destination'], six.string_types):
            msg = '{0} requires a string "destination" argument. Got: {1}'.\
                format(ct, args.get('destination'))
            raise exceptions.CommandException(msg)
        destination = args['destination']

        if not os.path.isdir(destination):
            msg = '{0}: Specified "destination" directory "{1}" doesn\'t exist!'.\
                format(ct, destination)
            raise exceptions.CommandException(msg)

        data = {}
        if 'data' in args and isinstance(args['data'], dict):
            data = args['data']
        logger.debug('Template context data: {0}'.format(data))

        overwrite = args.get('overwrite', False)
        overwrite = True if str(overwrite).lower() in ['true', 'yes'] else False

        return (template, destination, data, overwrite)

    @classmethod
    def run(cls, c):
        # Transform list of dicts (where keys are unique) into a single dict
        args = c.input_res
        logger.debug('Jinja2Runner args={0}'.format(repr(args)))

        # Create a jinja environment
        logger.debug('Using templates dir: {0}'.format(c.files_dir))
        env = jinja2.Environment(loader=jinja2.FileSystemLoader(c.files_dir))
        env.trim_blocks = True
        env.lstrip_blocks = True
        template, destination, data, overwrite = cls._try_obtain_common_params(c)

        if c.comm_type == 'jinja_render':
            given_output = args.get('output', '')
            if not isinstance(given_output, six.string_types):
                raise exceptions.CommandException('Jinja2Runner: output must be string, got {0}'.\
                    format(given_output))
            result_fn = cls._make_output_file_name(destination, template, given_output)
            cls._render_one_template(env, template, result_fn, data, overwrite)
        elif c.comm_type == 'jinja_render_dir':
            cls._render_dir(env, template, destination, data, overwrite)

        return (True, 'success')

    @classmethod
    def _render_one_template(cls, env, template, result_filename, data, overwrite):
        # Get a template instance
        tpl = None
        try:
            logger.debug('Using template file: {0}'.format(template))
            tpl = env.get_template(template)
        except jinja2.TemplateNotFound as e:
            raise exceptions.CommandException('Template {t} not found in path {p}.'.\
                    format(t=template, p=env.loader.searchpath))
        except jinja2.TemplateError as e:
            raise exceptions.CommandException('Template file failure: {0}'.format(e.message))

        # Check if destination file exists, overwrite if needed
        if os.path.exists(result_filename):
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

    @classmethod
    def _render_dir(cls, env, template_dir, destination, data, overwrite):
        template_basedir = env.loader.searchpath[0]
        to_walk = os.path.join(template_basedir, template_dir)
        for dirpath, dirnames, filenames in os.walk(to_walk):
            for f in filenames:
                # get filename of template relative to template_dir
                tpl_name = cls._strip_dir_prefix(template_basedir, os.path.join(dirpath, f))
                dest_name = cls._make_output_file_name(destination,
                                         cls._strip_dir_prefix(template_dir, tpl_name))
                # if needed, create the dir that will contain the template
                dest_dir = os.path.dirname(dest_name)
                if not os.path.exists(dest_dir):
                    os.makedirs(dest_dir)

                cls._render_one_template(env, tpl_name, dest_name, data, overwrite)

    @classmethod
    def _strip_dir_prefix(cls, prefix, path):
        """Strips given prefix from given path, e.g.:
        if prefix == '/foo/bar/' and path == '/foo/bar/baz/spam', this returns 'baz/spam'
        """
        return path[len(prefix):].strip(os.path.sep)


@register_command_runner
class AsUserCommandRunner(CommandRunner):
    @classmethod
    def matches(cls, c):
        return c.comm_type.startswith('as ')

    @classmethod
    def get_user_from_comm_type(cls, comm_type):
        split_type = comm_type.split()
        if len(split_type) != 2:
            raise exceptions.CommandException('"as" expects format "as <username>".')
        user = split_type[1]
        return user

    @classmethod
    def run(cls, c):
        user = cls.get_user_from_comm_type(c.comm_type)
        to_run = utils.cl_string_for_da_eval(c.comm, c.kwargs)
        def sub_da_logger(msg):
            logger.info(msg, extra={'event_type': 'sub_da'})

        try:
            out = ClHelper.run_command(to_run, output_callback=sub_da_logger, as_user=user)
            ret = True
        except exceptions.ClException as e:
            out = e.output
            ret = False
        return [ret, out]


@register_command_runner
class DockerCommandRunner(object):
    _has_docker_group = None

    @classmethod
    def matches(cls, c):
        return c.comm_type.startswith('docker_')

    @classmethod
    def _docker_group_active(cls):
        if cls._has_docker_group is None:
            logger.debug('Determining if current user has active "docker" group ...')
            # we have to run cl command, too see if the user has already re-logged
            # after being added to docker group, so that he can effectively use it
            if 'docker' in ClHelper.run_command('groups').split():
                logger.debug('Current user is in "docker" group.')
                cls._has_docker_group = True
            else:
                logger.debug('Current user is not in "docker" group.')
                cls._has_docker_group = False
        return cls._has_docker_group

    @classmethod
    def _docker_group_added(cls):
        username = getpass.getuser()
        return username in grp.getgrnam('docker').gr_mem

    @classmethod
    def _docker_group_add(cls):
        username = getpass.getuser()
        try:
            logger.info('Adding {0} to group docker ...'.format(username))
            ClHelper.run_command('bash -c "usermod -a -G docker {0}"'.format(username),
                                 as_user='root')
        except exceptions.ClException as e:
            msg = 'Failed to add user to "docker" group: {0}'.format(e.output)
            raise exceptions.CommandException(msg)

    @classmethod
    def _cmd_for_newgrp(cls, command):
        """This formats given command to run under docker group, assuming that user has
        been added to it without logging out. If user has already re-logged, it doesn't
        alter the command.
        It uses double newgrp call (the first one adds user to docker group, but also
        sets docker to primary group, so we need to set the primary group back using
        another newgrp call.
        """
        if cls._docker_group_active():
            return command

        curgrp = grp.getgrgid(os.getegid()).gr_name
        template = [
            'cat << DA_DOCKER_OUTER_EOF | newgrp docker',
            'cat << DA_DOCKER_INNER_EOF | newgrp {curgrp}',
            '{command}',
            'DA_DOCKER_INNER_EOF',
            'DA_DOCKER_OUTER_EOF',
        ]
        return '\n'.join(template).format(curgrp=curgrp, command=command)

    @classmethod
    def _docker_service_running(cls):
        try:
            ClHelper.run_command('systemctl status docker')
            return True
        except exceptions.ClException:
            return False

    @classmethod
    def _docker_service_enable_and_run(cls):
        # TODO: add some conditionals for various platforms
        logger.info('Enabling and running docker service ...')
        try:
            cmd_str = 'bash -c "systemctl enable docker && systemctl start docker"'
            ClHelper.run_command(cmd_str, as_user='root')
        except exceptions.ClException:
            raise exceptions.CommandException('Failed to enable and run docker service.')

        # we need to wait until /var/run/docker.sock is created
        # let's wait for 30 seconds
        logger.info('Waiting for /var/run/docker.sock to be created (max 15 seconds) ...')
        success = False
        for i in range(0, 30):
            time.sleep(i * 0.5)
            try:
                ClHelper.run_command('ls /var/run/docker.sock')
                success = True
                break
            except exceptions.ClException:
                pass

        if not success:
            logger.warning('/var/run/docker.sock doesn\'t exist, docker will likely not work!')

    @classmethod
    def run(cls, c):
        """Only users in "docker" group can use docker; there are three possible situations:
        1) user is not added to docker group => we need to add him there and then go to 2)
        2) user has been added to docker group, but would need to log out for it to
           take effect => use "newgrp" (_cmd_for_newgrp) for all docker commands
        3) user has been added to docker group in a previous login session => all ok
        """
        if not cls._docker_group_active() and not cls._docker_group_added():
            # situation 1
            cls._docker_group_add()
        # else situation 3

        if not cls._docker_service_running():
            cls._docker_service_enable_and_run()

        if c.comm_type == 'docker_build':
            # TODO: allow providing another argument - a repository name/tag for the built image
            ret = cls._docker_build(c.input_res)
        elif c.comm_type == 'docker_run':
            ret = cls._docker_run(c.input_res)
        elif c.comm_type == 'docker_attach':
            ret = cls._docker_attach(c.input_res)
        elif c.comm_type == 'docker_find_img':
            ret = cls._docker_find_image(c.input_res)
        elif c.comm_type == 'docker_container_ip':
            ret = cls._docker_get_container_attr('{{.NetworkSettings.IPAddress}}', c.input_res)
        elif c.comm_type == 'docker_container_name':
            ret = cls._docker_get_container_attr('{{.Name}}', c.input_res)
        else:
            raise exceptions.CommandException('Unknown command type {ct}.'.format(ct=c.comm_type))

        return ret

    @classmethod
    def _docker_build(cls, directory):
        logger.info('Building Docker image, this may take a while ...')
        logres = False
        final_image = ''

        cmd_str = cls._cmd_for_newgrp('docker build --rm {0}'.format(directory))
        try:
            result = ClHelper.run_command(cmd_str, log_level=logging.INFO)

            success_re = re.compile(r'Successfully built ([0-9a-f]+)')
            success_found = success_re.search(result)
            if success_found:
                logres = True
                final_image = success_found.group(1)
        except exceptions.ClException:
            pass  # no-op

        return (logres, final_image)

    @classmethod
    def _get_docker_run_args(cls, inp):
        if not isinstance(inp, dict):
            raise exceptions.CommandException('docker_r expects mapping as input.')
        if not 'image' in inp:
            raise exceptions.CommandException('docker_r requires "image" argument.')

        return {'image': inp['image'], 'args': inp.get('args', '')}

    @classmethod
    def _docker_run(cls, inp):
        # TODO: we need to register the container for shutdown at DA exit, if run as daemon
        run_args = cls._get_docker_run_args(inp)
        logres = False
        res = ''

        cmd_str = cls._cmd_for_newgrp('docker run {args} {image}'.format(**run_args))
        try:
            res = ClHelper.run_command(cmd_str)
            logres = True
        except exceptions.ClException:
            pass  # no-op

        return (logres, res)

    @classmethod
    def _docker_attach(cls, container_hash):
        result = ''
        logres = False

        cmd_str = cls._cmd_for_newgrp('docker attach {0}'.format(container_hash))
        try:
            result = ClHelper.run_command(cmd_str, log_level=logging.INFO)
            logres = True
        except exceptions.ClException as e:
            # even if there is error, return container output
            result = e.output

        return (logres, result)

    @classmethod
    def _docker_find_image(cls, hash_start):
        found_hashes = []

        cmd_str = cls._cmd_for_newgrp('docker images -q --no-trunc')
        try:
            result = ClHelper.run_command(cmd_str)

            for line in result.splitlines():
                if line.startswith(hash_start):
                    found_hashes.append(line.strip())
        except exceptions.ClException:
            pass  # no-op

        found_hash = ' '.join(found_hashes)
        # return True if there was precisely one hash found
        logres = ' ' not in found_hash and found_hash
        return (logres, found_hash)

    @classmethod
    def _docker_get_container_attr(cls, attr, container_hash):
        logres = False
        res = ''

        cmd_str = "docker inspect --format='{attr}' {cont}".format(attr=attr,
                                                                   cont=container_hash)
        cmd_str = cls._cmd_for_newgrp(cmd_str)
        try:
            res = ClHelper.run_command(cmd_str)
            logres = True
        except exceptions.ClException:
            pass  # no-op

        return (logres, res)


@register_command_runner
class NormalizeCommandRunner(CommandRunner):
    @classmethod
    def matches(cls, c):
        return c.comm_type == 'normalize'

    @classmethod
    def run(cls, c):
        """Normalizes c.input_res (string):

        - removes digit from start
        - replaces dashes and whitespaces with underscores
        """
        to_norm = c.input_res
        if not isinstance(to_norm, six.string_types):
            raise exceptions.CommandException('"normalize" expects string input, got {0}'.\
                format(to_norm))

        normalized = to_norm.lstrip('0123456789')
        badchars = '-+\\|()[]{}<>,./:\'" \t;`!@#$%^&*'
        if sys.version_info[0] < 3:
            tt = string.maketrans(badchars, '_' * len(badchars))
        else:
            tt = str.maketrans(badchars, '_' * len(badchars))
        normalized = normalized.translate(tt)
        return (True, normalized)


@register_command_runner
class SetupProjectDirCommandRunner(CommandRunner):
    @classmethod
    def matches(cls, c):
        return c.comm_type == 'setup_project_dir'

    @classmethod
    def _get_args(cls, inp, ctxt):
        args = {}
        if not isinstance(inp, dict):
            raise exceptions.CommandException('"setup_project_dir" expects mapping as input')

        args['from'] = inp.get('from', None)
        if args['from'] is None:
            raise exceptions.CommandException('"setup_project_dir" requires "from" argument')

        args['contdir_var'] = inp.get('contdir_var', 'contdir')
        args['topdir_var'] = inp.get('topdir_var', 'topdir')
        args['topdir_normalized_var'] = inp.get('topdir_normalized_var', 'topdir_normalized')
        args['accept_path'] = bool(inp.get('accept_path', True))
        args['create_topdir'] = inp.get('create_topdir', True)
        if not args['create_topdir'] in [True, False, 'normalized']:
            msg = '"setup_project_dir" expects "create_topdir" to be one of: ' +\
                'True, False, normalized'
            raise exceptions.CommandException(msg)
        args['on_existing'] = inp.get('on_existing', 'fail')
        if not args['on_existing'] in ['fail', 'pass']:
            msg = '"setup_project_dir" expects "on_existing" to be one of: "fail", "pass"'
            raise exceptions.CommandException(msg)

        return args

    @classmethod
    def run(cls, c):
        args = cls._get_args(c.input_res, c.kwargs)
        contdir, topdir = os.path.split(args['from'])
        normalized_topdir = lang.Command('normalize', topdir).run()[1]
        try:  # ok, this is a bit ugly, but we need to check multiple calls for the exception
            if contdir:  # we need to create containing directory
                if not args['accept_path']:
                    msg = 'Path is not accepted as project name by this assistant (got "{0}")'
                    raise exceptions.CommandException(msg.format(args['from']))

                if not os.path.exists(contdir):
                    os.makedirs(contdir)
                elif not os.path.isdir(contdir):
                    msg = 'Can\'t create subdirectory in "{0}", it\'s not a directory'.\
                        format(contdir)
                    raise exceptions.CommandException(msg)
            actual_topdir = normalized_topdir if args['create_topdir'] == 'normalized' else topdir
            topdir_fullpath = os.path.join(contdir, actual_topdir)
            if args['create_topdir']:
                if os.path.exists(topdir_fullpath):
                    if args['on_existing'] == 'fail':
                        msg = 'Directory "{0}" already exists, can\'t proceed'.format(topdir_fullpath)
                        raise exceptions.CommandException(msg)
                    elif not os.path.isdir(topdir_fullpath):
                        msg = 'Location "{0}" exists, but is not a directory, can\'t proceed'.\
                            format(topdir_fullpath)
                        raise exceptions.CommandException(msg)
                else:
                    os.makedirs(topdir_fullpath)

        except OSError as e:
            msg = 'Failed to create directory {0}: {1}'.format(args['from'], e.message)
            raise CommandException(msg)

        # if contdir == '', then return current dir ('.')
        c.kwargs[args['contdir_var']] = contdir or '.'
        c.kwargs[args['topdir_var']] = topdir
        c.kwargs[args['topdir_normalized_var']] = normalized_topdir

        return (True, topdir_fullpath if args['create_topdir'] else contdir)
