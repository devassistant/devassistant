import itertools
import logging
import os
import subprocess
import sys
import yaml

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

from devassistant import argument
from devassistant import bin
from devassistant import dapi
from devassistant import exceptions
from devassistant import lang
from devassistant import settings
from devassistant import utils
from devassistant.assistant_base import AssistantBase
from devassistant.dapi import dapicli
from devassistant.logger import logger

actions = {}


def register_action(action):
    """Decorator that adds an action class to active actions.
    Only toplevel actions should be registered, subactions will be
    read from Action.get_subactions()."""
    actions[action] = _register_actions_recursive(action, {})
    return action


def _register_actions_recursive(action, subact_dict):
    for a in action.get_subactions():
        subact_dict[a] = {}
        _register_actions_recursive(a, subact_dict[a])
    return subact_dict


def is_action_run(**kwargs):
    first_act = kwargs.get(settings.SUBASSISTANT_N_STRING.format(0), None)
    if first_act in map(lambda a: a.name, actions.keys()):
        return True
    return False


def get_action_to_run(level=0, **kwargs):
    return _get_action_to_run_recursive(level, actions, **kwargs)


def _get_action_to_run_recursive(level, subact_dict, **kwargs):
    alevel = settings.SUBASSISTANT_N_STRING.format(level)
    aname = kwargs.get(alevel, None)
    if not aname:
        return None
    for a, suba in subact_dict.items():
        if a.name == aname:
            if settings.SUBASSISTANT_N_STRING.format(level + 1) in kwargs:
                return _get_action_to_run_recursive(level + 1, suba, **kwargs)
            else:
                return a


class Action(object):
    """Superclass of custom actions of devassistant"""

    name = 'action'
    description = 'Action description'
    args = []
    hidden = False

    def __init__(self, **kwargs):
        """Instantiate an action, accepts arguments parsed from cli/retrieved from gui."""
        self.kwargs = kwargs

    @classmethod
    def get_subactions(cls):
        return []

    def run(self):
        """Runs this action.

        Raises:
            devassistant.exceptions.ExecutionExceptions if something goes wrong
        """
        raise NotImplementedError()


@register_action
class DocAction(Action):
    name = 'doc'
    description = 'Display documentation for a DAP package.'
    args = [argument.Argument('dap', 'dap', choices=sorted(dapicli.get_installed_daps()),
                              help='Packages to get documentation for'),
            argument.Argument('doc', 'doc', nargs='?', help='Document to display')]

    def run(self):
        dap = self.kwargs['dap']
        doc = self.kwargs.get('doc', None)
        docdir = utils.find_file_in_load_dirs(os.path.join('doc', dap))
        all_docs = []
        if docdir is not None:
            all_docs = self._get_doc_files(docdir)
        if not all_docs:
            logger.info('DAP {0} has no documentation.'.format(dap))
        elif doc is not None:
            doc_fullpath = os.path.join(docdir, doc)
            if doc_fullpath in all_docs:
                self._show_doc(doc_fullpath)
            else:
                msg = 'DAP {0} has no document "{1}".'.format(dap, doc)
                logger.error(msg)
                raise exceptions.ExecutionException(msg)
        else:
            logger.info('DAP {0} has these docs:'.format(dap))
            for d in all_docs:
                logger.info(d[len(docdir):].strip(os.path.sep))
            logger.info('Use "da doc {0} <DOC>" to see a specific document'.format(dap))

    @classmethod
    def _get_doc_files(cls, docdir):
        found = []
        for root, dirs, files in os.walk(docdir):
            found.extend([os.path.join(root, f) for f in files])
        return sorted(found)

    @classmethod
    def _show_doc(cls, fullpath):
        have_less = True
        try:
            subprocess.check_call(['which', 'less'], stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT)
        except (subprocess.CalledProcessError, OSError):
            have_less = False
        if have_less:
            subprocess.Popen(['less', '-F', '-R', '-S', '-X', '-K', fullpath],
                             stdin=subprocess.PIPE, stdout=sys.stdout).communicate()
        else:
            logger.info(open(fullpath).read())


@register_action
class EvalAction(Action):
    name = 'eval'
    description = 'Evaluate input containing Yaml code and context. Internal use only.'
    args = [argument.Argument('input', 'input')]
    hidden = True

    def run(self):
        to_run = self.gather_input(self.kwargs['input'])
        parsed = yaml.load(to_run, Loader=Loader)
        lang.run_section(parsed.get('run', []), parsed.get('ctxt', {}))

    @classmethod
    def gather_input(cls, received):
        if received == '-':
            # read from stdin
            to_run = []
            for l in sys.stdin.readlines():
                to_run.append(l)
            to_run = ''.join(to_run)
        else:
            to_run = received
        return to_run


@register_action
class HelpAction(Action):
    """Can gather info about all actions and assistant types and print it nicely."""
    name = 'help'
    description = 'Print detailed help.'

    def run(self):
        """Prints nice help."""
        print(HelpAction.get_help(format_type=self.kwargs.get('format_type')))

    @classmethod
    def get_help(cls, format_type=None):
        """Constructs and formats help for printing.

        Args:
            format_type: type of formatting for nice output, see format_text for possible values
        """
        # we set default format type here because we might get None from .run()
        if not format_type:
            format_type = 'ascii'

        top_visible_actions = list(filter(lambda a: not a.hidden, actions))
        # we will justify the action names (and assistant types) to the same width
        just = max(
            max(*map(lambda x: len(x), settings.ASSISTANT_ROLES)),
            max(*map(lambda x: len(x.name), top_visible_actions))
        ) + 2
        text = ['You can either run assistants with:']
        text.append(cls.format_text('da [--debug] {create,tweak,prepare,extras} ' +
                                    '[ASSISTANT [ARGUMENTS]] ...',
                                    'bold',
                                    format_type))
        text.append('')
        text.append('Where:')
        text.append(cls.format_action_line('create',
                                           'used for creating new projects',
                                           just,
                                           format_type))
        text.append(cls.format_action_line('tweak',
                                           'used for working with existing projects',
                                           just,
                                           format_type))
        text.append(cls.format_action_line('prepare',
                                           'used for preparing environment for upstream projects',
                                           just,
                                           format_type))
        text.append(cls.format_action_line('extras',
                                           'used for performing custom tasks not related to a '
                                           'specific project',
                                           just,
                                           format_type))
        text.append('You can shorten "create" to "crt", "tweak" to "twk" ' +
                    'and "extras" to "extra".')
        text.append('')
        text.append('Or you can run a custom action:')
        text.append(cls.format_text('da [--debug] [ACTION] [ARGUMENTS]',
                                    'bold',
                                    format_type))
        text.append('')
        text.append('Available actions:')
        for action in sorted(top_visible_actions, key=lambda x: x.name):
            text.append(cls.format_action_line(action.name,
                                               action.description,
                                               just,
                                               format_type))
        return '\n'.join(text)

    @classmethod
    def format_text(cls, text, format, format_type):
        """Formats text to have given format in given format_type.

        Args:
            text: text to format
            format: format, e.g. 'bold'
            format_type: None (will do nothing) or 'ascii'
        Returns:
            formatted text
        """
        if format_type == 'ascii':
            if format == 'bold':
                text = '\033[1m' + text + '\033[0m'
        return text

    @classmethod
    def format_action_line(cls, action_name, action_desc, just, format_type):
        """Creates and formats action line from given action_name and action_desc.

        Args:
            action_name: name of action
            action_desc: description of action
            just: columns to justify action_name to
            format_type: formats action_name in bold using this format, see
                         format_text help for available format types
        Returns:
            formatted action line
        """
        text = []
        justed_name = action_name.ljust(just)
        text.append(cls.format_text(justed_name, 'bold', format_type))
        text.append(action_desc)
        return ''.join(text)


class PkgInstallAction(Action):
    """Installs packages from Dapi"""
    name = 'install'
    description = 'Installs packages from DAPI or from given paths.'
    args = [
        argument.Argument('package', 'package', nargs='+', help='Packages to install'),
        argument.Argument('force', '-f', '--force', action='store_true', default=False,
                          help='Install packages that are unsupported on this platform (dangerous)'
                          ),
        argument.Argument('nodeps', '-n', '--no-deps', action='store_true', default=False,
                          help='Do not install dependencies of the selected package'),
        argument.Argument('reinstall', '-r', '--reinstall', action='store_true', default=False,
                          help='If the package is already installed, reinstall it'),
    ]

    def run(self):
        exs = []
        for pkg in self.kwargs['package']:
            logger.info('Installing DAP {pkg} ...'.format(pkg=pkg))
            if os.path.isfile(pkg):
                method = dapicli.install_dap_from_path
            else:
                method = dapicli.install_dap
            try:
                pkgs = method(pkg, force=self.kwargs['force'],
                              nodeps=self.kwargs['nodeps'], reinstall=self.kwargs['reinstall'],
                              __ui__=self.kwargs['__ui__'])
                logger.info('Successfully installed DAPs {pkgs}'.format(pkgs=' '.join(pkgs)))
            except exceptions.DapiError as e:
                exs.append(utils.exc_as_decoded_string(e))
                logger.error(utils.exc_as_decoded_string(e))
        if exs:
            raise exceptions.ExecutionException('; '.join(exs))


class PkgUninstallAction(Action):
    """Uninstalls packages from Dapi"""
    name = 'uninstall'
    description = 'Uninstalls DAP packages of given names.'
    args = [
        argument.Argument('package', 'package', nargs='+', help='Package(s) to uninstall'),
        argument.Argument('force', '-f', '--force', action='store_false',
                          default=True, help='Do not ask for confirmation'),
        argument.Argument('allpaths', '-a', '--all-paths', action='store_true',
                          default=False, help='Try to uninstall from all possible locations'),
    ]

    def run(self):
        exs = []
        uninstalled = []
        for pkg in self.kwargs['package']:
            if pkg in uninstalled:
                logger.info('DAP {pkg} already uninstalled'.format(pkg=pkg))
                continue
            logger.info('Uninstalling DAP {pkg} ...'.format(pkg=pkg))
            try:
                done = dapicli.uninstall_dap(pkg, confirm=self.kwargs['force'],
                                             allpaths=self.kwargs['allpaths'],
                                             __ui__=self.kwargs['__ui__'])
                if done:
                    logger.info('DAPs {pkgs} successfully uninstalled'.format(pkgs=' '.join(done)))
                    uninstalled += done
            except exceptions.DapiError as e:
                exs.append(utils.exc_as_decoded_string(e))
                logger.error(utils.exc_as_decoded_string(e))
        if exs:
            raise exceptions.ExecutionException('; '.join(exs))


class PkgRemoveAction(PkgUninstallAction):
    """Alias for uninstall"""
    name = 'remove'
    description = 'An alias for uninstall command'
    # TODO: implement aliases for actions


class PkgUpdateAction(Action):
    """Updates packages from Dapi"""
    name = 'update'
    description = 'Updates DAP packages of given names or all local packages.'
    args = [
        argument.Argument('package', 'package', nargs='*',
                          help='Packages to update - if none are provided,'
                               'all local packages are updated'),
        argument.Argument('force', '-f', '--force', action='store_true', default=False,
                          help='Update and install dependent packages'
                               'that are unsupported on this platform (dangerous)'),
        argument.Argument('allpaths', '-a', '--all-paths', action='store_true', default=False,
                          help='Try to update packages in all paths'),
    ]

    def run(self):
        pkgs = exs = []
        try:
            pkgs = self.kwargs['package']
        except KeyError:
            pkgs = dapicli.get_installed_daps()
            if pkgs:
                logger.info('Updating all DAP packages ...')
            else:
                logger.info('No installed DAP packages found, nothing to update.')
        for pkg in pkgs:
            logger.info('Updating DAP {pkg} ...'.format(pkg=pkg))
            try:
                updated = dapicli.install_dap(pkg,
                                              update=True,
                                              update_allpaths=self.kwargs['allpaths'],
                                              force=self.kwargs['force'])
                if updated:
                    logger.info('DAP {pkg} successfully updated.'.format(pkg=pkg))
                else:
                    logger.info('DAP {pkg} is already up to date.'.format(pkg=pkg))
            except exceptions.DapiError as e:
                exs.append(utils.exc_as_decoded_string(e))
                logger.error(utils.exc_as_decoded_string(e))
        if exs:
            raise exceptions.ExecutionException('; '.join(exs))


class PkgListAction(Action):
    """List installed packages from Dapi"""
    name = 'list'
    description = 'Lists DAP packages, installed or available.'
    args = [
        argument.Argument('simple', '-s', '--simple', action='store_true', default=False,
                          help='List only the names of packages'),
        argument.Argument('installed', '-i', '--installed', action='store_true', default=False,
                          help='List installed packages (default)'),
        argument.Argument('remote', '-r', '--remote', action='store_true', default=False,
                          help='List all packages from DAPI'),
        argument.Argument('available', '-a', '--available', action='store_true', default=False,
                          help='List packages available from DAPI (not installed only)'),
    ]

    def run(self):
        if [self.kwargs[k] for k in ['installed', 'remote', 'available']].count(True) > 1:
            logger.error('Only one of --installed, --remote or --available '
                         'can be used simultaneously')
            return
        if self.kwargs['remote'] or self.kwargs['available']:
            logger.infolines(dapicli.format_daps(simple=self.kwargs['simple'],
                             skip_installed=self.kwargs['available']))
        else:
            logger.infolines(dapicli.format_installed_dap_list(simple=self.kwargs['simple']))


class PkgSearchAction(Action):
    """Search packages from Dapi"""
    name = 'search'
    description = 'Searches packages on DAPI for given term(s) and prints the result.'
    args = [
        argument.Argument('query', 'query', nargs='+', help='One or multiple search queries'),
        argument.Argument('noassistants', '-a', '--noassistants',
                          help='Include DAPs without Assistants',
                          default=False, action='store_true'),
        argument.Argument('unstable', '-u', '--unstable',
                          help='Include DAPs without stable release',
                          default=False, action='store_true'),
        argument.Argument('deactivated', '-d', '--deactivated', help='Include deactivated DAPs',
                          default=False, action='store_true'),
        argument.Argument('minrank', '-r', '--minrank',
                          help='Search only for DAPs with given or greater rank', default=0),
        argument.Argument('mincount', '-c', '--mincount',
                          help='Search only for DAPs that have been ranked at least given time',
                          default=0),
        argument.Argument('allplatforms', '-p', '--all-platforms',
                          help='Include DAPs unsupported on this platform',
                          default=False, action='store_true'),
    ]

    def run(self):
        newargs = {}
        newargs['q'] = ' '.join(self.kwargs['query'])
        newargs['noassistants'] = self.kwargs['noassistants']
        newargs['unstable'] = self.kwargs['unstable']
        newargs['notactive'] = self.kwargs['deactivated']
        newargs['minimal_rank'] = self.kwargs['minrank']
        newargs['minimal_rank_count'] = self.kwargs['mincount']
        if not self.kwargs['allplatforms']:
            newargs['platform'] = utils.get_distro_name()

        try:
            logger.infolines(dapicli.format_search(**newargs))
        except exceptions.DapiError as e:
            logger.error(utils.exc_as_decoded_string(e))
            raise exceptions.ExecutionException(utils.exc_as_decoded_string(e))


class PkgInfoAction(Action):
    """Prints information about packages from Dapi"""
    name = 'info'
    description = 'Prints information about packages from DAPI.'
    args = [argument.Argument('package', 'package', help='Package to print info for'),
            argument.Argument('full', '--full', help='More information (useful for developers)',
                              required=False, action='store_true'),
            argument.Argument('installed', '--installed', help='Query installed package',
                              required=False, action='store_true')]

    def run(self):
        if os.path.isfile(self.kwargs['package']):
            old_level = logger.getEffectiveLevel()
            logger.setLevel(logging.ERROR)
            try:
                d = dapi.Dap(self.kwargs['package'])
                if not dapi.DapChecker.check(d):
                    raise exceptions.ExecutionException(
                        'This DAP is not valid, info can\'t be displayed.')
            finally:
                logger.setLevel(old_level)
            logger.infolines(dapicli.format_local_dap(d, full=self.kwargs.get('full', False)))
        elif self.kwargs.get('installed'):
            try:
                logger.infolines(dapicli.format_installed_dap(self.kwargs['package'],
                                                              full=self.kwargs.get('full', False)))
            except exceptions.DapiError as e:
                logger.error(utils.exc_as_decoded_string(e))
                raise exceptions.ExecutionException(utils.exc_as_decoded_string(e))
        else:
            try:
                logger.infolines(dapicli.format_dap_from_dapi(self.kwargs['package'],
                                                              full=self.kwargs.get('full', False)))
            except exceptions.DapiError as e:
                logger.error(utils.exc_as_decoded_string(e))
                raise exceptions.ExecutionException(utils.exc_as_decoded_string(e))


class PkgLintAction(Action):
    """Checks packages for sanity"""
    name = 'lint'
    description = 'Checks local DAP packages for sanity.'
    args = [
        argument.Argument('package', 'package', nargs='+',
                          help='One or multiple packages to check (path)'),
        argument.Argument('network', '-n', '--network', action='store_true', default=False,
                          help='Perform checks that require Internet connection'),
        argument.Argument('nowarnings', '-w', '--nowarnings', action='store_true', default=False,
                          help='Ignore warnings'),
        argument.Argument('noyamlcheck', '-y', '--noyamlcheck', action='store_true', default=False,
                          help='Don\'t perform YAML checks on Assistants and Snippets'),
    ]

    def run(self):
        error = False
        old_level = logger.getEffectiveLevel()
        for pkg in self.kwargs['package']:
            try:
                if self.kwargs['nowarnings']:
                    logger.setLevel(logging.ERROR)
                d = dapi.Dap(pkg)
                if not dapi.DapChecker.check(d, network=self.kwargs['network'],
                                             yamls=not self.kwargs['noyamlcheck']):
                    error = True
            except (exceptions.DapFileError, exceptions.DapMetaError) as e:
                logger.error(utils.exc_as_decoded_string(e))
                error = True
        logger.setLevel(old_level)
        if error:
            raise exceptions.ExecutionException('One or more packages are not sane')


@register_action
class PkgAction(Action):
    """Manage packages"""
    name = 'pkg'
    description = 'Lets you interact with online DAPI service and your local DAP packages.'

    @classmethod
    def get_subactions(cls):
        return [
            PkgInstallAction,
            PkgUninstallAction,
            PkgRemoveAction,
            PkgUpdateAction,
            PkgListAction,
            PkgSearchAction,
            PkgInfoAction,
            PkgLintAction,
        ]


@register_action
class VersionAction(Action):
    """Prints DevAssistant version, what else?"""
    name = 'version'
    description = 'Print version'

    def run(self):
        from devassistant import __version__
        logger.info('DevAssistant {version}'.format(version=__version__))

@register_action
class AutoCompleteAction(Action):
    """Outputs strings for bash completion"""
    name = 'autocomplete'
    description = 'Provide appropriate strings for bash completion'
    args = [argument.Argument('path', 'path', default='', nargs='?')]
    hidden = True

    _assistant_names = ['create', 'tweak', 'prepare', 'extra']
    _special_tokens = ['--debug']

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self._assistants = bin.TopAssistant().get_subassistants()
        self._actions = [action for action in actions if not action.hidden]

    def run(self):
        # Assistant names are hardcoded here because on the root level, we only
        # want to show these nice long forms. All forms incl. old aliases are
        # autocompleted, of course.
        flags = self._get_flags_for_path(self.kwargs.get('path', '').split())
        print(' '.join(flags))

    def _get_flags_for_path(self, path):
        '''For a given path, separated by spaces, return a list of completable paths.
        Commencing dashes in flags are expected to be replaced with underscores
        (to fool argparse into not parsing those)'''
        path = [tok[:2].replace('_', '-') + tok[2:] for tok in path]

        # No path specified
        if not path or (len(path) == 1 and path[0] in self._special_tokens):
            flags = self._assistant_names + [a.name for a in self._actions] + \
                    self._special_tokens + ['--help']

        else:
            elem = self._get_elem_for_path(path)
            if elem:
                flags = self._get_flags(elem, long_only=True) + \
                        [a.name for a in self._get_descendants(elem)] + \
                        ['--help']

                #TODO Fix so that it honors nargs
                # Last argument in flags or there are positional arguments
                if path[-1] in self._get_flags(elem, dashed_only=True, attributes_only=True) \
                    or self._get_positional_args(elem):
                    flags.append('_FILENAMES')
            else:
                flags = []

        return sorted(flags)

    def _get_elem_for_path(self, path):
        '''Get element (Assistant or Action) specified by given path'''
        skipping = False
        result = None
        current = self._assistants + self._actions
        for token in path:
            found = False if not skipping else True

            if token in self._special_tokens:
                continue

            # If result has positional arguments or token is a flag, it's safe
            # to skip until next valid token is found
            if result and \
                    (self._get_positional_args(result) \
                    or token in self._get_flags(result, dashed_only=True)):
                skipping = True
                found = True
                continue

            # Searching descendants
            for elem in current:
                try:
                    aliases = elem.aliases
                except AttributeError:
                    aliases = []
                if token == elem.name or token in aliases:
                    found = True
                    skipping = False
                    current = self._get_descendants(elem)
                    result = elem
                    break

            if found or skipping:
                continue
            else:
                break

        return result if found or skipping else None

    @classmethod
    def _get_descendants(cls, elem):
        '''Get descendants for and Assistant or Action (or anything possessing
        the method get_subactions() or get_subassistants())'''
        try:
            return elem.get_subassistants()
        except AttributeError:
            pass
        try:
            return elem.get_subactions()
        except AttributeError:
            pass

        raise TypeError('Element must be an Action or Assistant, is {t}'.format(t=elem))


    @classmethod
    def _get_flags(cls, elem, dashed_only=False, long_only=False, attributes_only=False):
        '''Get flags for arguments of a given element (Assistant or Action). Optionally may
        be restricted only to flags starting with one or two dashes.'''
        args = elem.args
        if attributes_only:
            args = cls._get_args_with_attributes(args)

        result = list(itertools.chain(*[arg.flags for arg in args]))
        if dashed_only:
            result = [flag for flag in result if flag.startswith('-')]
        if long_only:
            result = [flag for flag in result if flag.startswith('--')]

        return result

    @classmethod
    def _get_args_with_attributes(cls, args):
        '''Get arguments that require attributes'''
        return [a for a in args if not str(a.kwargs.get('action', '')).startswith('store_')]

    @classmethod
    def _get_positional_args(cls, elem):
        '''Get positional arguments of elem'''
        return [a for a in cls._get_args_with_attributes(elem.args) \
                        if not [f for f in a.flags if f.startswith('-')]]
