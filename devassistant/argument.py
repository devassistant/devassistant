import getpass
import os
import re

from devassistant import exceptions
from devassistant import utils
from devassistant import yaml_snippet_loader
from devassistant.config_manager import config_manager


class Argument(object):
    """Represents assistant argument, that can either be added to argparse parser
    or interpreted otherwise by any frontend."""
    create_dest_pattern = re.compile(r'[\W]+')

    def __init__(self, name, *args, **kwargs):
        self.name = name
        self.flags = args
        self.gui_hints = kwargs.pop('gui_hints', {})
        self.kwargs = kwargs
        if 'help' not in self.kwargs:
            self.kwargs['help'] = '(No help provided)'
        if 'dest' not in self.kwargs:
            dest = self.name.replace('-', '_')
            dest = self.create_dest_pattern.sub('', dest)
            if len(args) == 1 and args[0][0] != '-':
                # positional argument => we have to replace the "flag" and not provide dest
                self.positional = True
                self.flags = [dest]
            else:
                self.positional = False
                self.kwargs['dest'] = dest

    def add_argument_to(self, parser):
        """Used by cli to add this as an argument to argparse parser.

        Args:
            parser: parser to add this argument to
        """
        from devassistant.cli.devassistant_argparse import DefaultIffUsedActionFactory
        if isinstance(self.kwargs.get('action', ''), list):
            # see documentation of DefaultIffUsedActionFactory to see why this is necessary
            if self.kwargs['action'][0] == 'default_iff_used':
                self.kwargs['action'] = DefaultIffUsedActionFactory.generate_action(
                    self.kwargs['action'][1])
        # In cli 'preserved' is not supported.
        # It needs to be removed because it is unknown for argparse.
        self.kwargs.pop('preserved', None)
        try:
            parser.add_argument(*self.flags, **self.kwargs)
        except Exception as ex:
            problem = "Error while adding argument '{name}': {error}".\
                format(name=self.name, error=repr(ex))
            raise exceptions.ExecutionException(problem)



    def get_dest(self):
        """Get "dest", which represents the name of this argument translated
        to proper name of Yaml DSL variable.
        """
        if self.positional:
            return self.flags[0]
        else:
            return self.kwargs['dest']

    def get_gui_hint(self, hint):
        """Returns the value for specified gui hint (or a sensible default value,
        if this argument doesn't specify the hint).

        Args:
            hint: name of the hint to get value for
        Returns:
            value of the hint specified in yaml or a sensible default
        """
        if hint == 'type':
            # 'self.kwargs.get('nargs') == 0' is there for default_iff_used, which may
            # have nargs: 0, so that it works similarly to 'store_const'
            if self.kwargs.get('action') == 'store_true' or self.kwargs.get('nargs') == 0:
                return 'bool'
            # store_const is represented by checkbox, but computes default differently
            elif self.kwargs.get('action') == 'store_const':
                return 'const'
            return self.gui_hints.get('type', 'str')
        elif hint == 'default':
            hint_type = self.get_gui_hint('type')
            hint_default = self.gui_hints.get('default', None)
            arg_default = self.kwargs.get('default', None)
            preserved_value = None
            if 'preserved' in self.kwargs:
                preserved_value = config_manager.get_config_value(self.kwargs['preserved'])

            if hint_type == 'path':
                if preserved_value is not None:
                    default = preserved_value
                elif hint_default is not None:
                    default = hint_default.replace('$(pwd)', utils.get_cwd_or_homedir())
                else:
                    default = arg_default or '~'
                return os.path.abspath(os.path.expanduser(default))
            elif hint_type == 'bool':
                return hint_default or arg_default or False
            elif hint_type == 'const':
                return hint_default or arg_default
            else:
                if hint_default == '$(whoami)':
                    hint_default = getpass.getuser()
                return preserved_value or hint_default or arg_default or ''

    @classmethod
    def construct_arg(cls, name, params):
        """Construct an argument from name, and params (dict loaded from assistant/snippet).
        """
        use_snippet = params.pop('use', None)
        if use_snippet:
            # if snippet is used, take this parameter from snippet and update
            # it with current params, if any
            try:
                problem = None
                snippet = yaml_snippet_loader.YamlSnippetLoader.get_snippet_by_name(use_snippet)
                # this works much like snippet.args.pop(arg_name).update(arg_params),
                # but unlike it, this actually returns the updated dict
                params = dict(snippet.args.pop(name), **params)
                # if there is SnippetNotFoundException, just let it be raised
            except KeyError:  # snippet doesn't have the requested argument
                problem = 'Couldn\'t find arg {arg} in snippet {snip}.'.\
                    format(arg=name, snip=snippet.name)
                raise exceptions.ExecutionException(problem)

        if 'flags' not in params:
            msg = 'Couldn\'t find "flags" in arg {arg}'.format(arg=name)
            raise exceptions.ExecutionException(msg)
        return cls(name, *params.pop('flags'), **params)
