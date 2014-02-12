import os

import six

from devassistant import exceptions
from devassistant import settings

class LoadedYaml(object):
    _yaml_typenames = {dict: 'mapping',
                       list: 'list',
                       six.text_type: 'string',
                       six.binary_type: 'string',
                       six.string_types: 'string'}

    @property
    def load_path(self):
        lp = ''
        for d in settings.DATA_DIRECTORIES:
            if d == os.path.commonprefix([self.path, d]): break

        return d

    def default_files_dir_for(self, files_subdir):
        yaml_path = self.path.replace(os.path.join(self.load_path, files_subdir), '')
        yaml_path = os.path.splitext(yaml_path)[0]
        yaml_path = yaml_path.strip(os.sep)
        parts = [self.load_path, 'files']
        if files_subdir == 'snippets':
            parts.append(files_subdir)
        parts.append(yaml_path)
        return os.path.join(*parts)

    def check(self):
        """Checks whether loaded yaml is well-formed according to syntax defined for
        version 0.9.0 and later.

        Raises:
            YamlError: (containing a meaningful message) when the loaded Yaml
                is not well formed
        """
        #self._check_fullname(self.path)
        #self._check_description(self.path)
        self._check_args(self.path)
        #self._check_dependencies(self.path)
        #self._check_run(self.path)

    def _check_fullname(self):
        raise NotImplementedError('_check_fullname not implemented in class {0}'.\
                format(type(self)))

    def _check_description(self):
        raise NotImplementedError('_check_description not implemented in class {0}'.\
                format(type(self)))

    def _check_args(self, source):
        args = self.parsed_yaml.get('args', {})
        self._assert_dict(args, 'args', [source])
        for argn, argattrs in args.items():
            pass

    def _check_dependencies(self):
        pass

    def _check_run(self):
        pass

    def _assert_dict(self, struct, name, path=None):
        self._assert_struct_type(struct, name, dict, path)

    def _assert_str(self, struct, name, path=None):
        self._assert_struct_type(struct, name, six.string_types, path)

    def _assert_list(self, struct, name, path=None):
        self._assert_struct_type(struct, name, list, path)

    def _assert_struct_type(self, struct, name, typ, path):
        wanted_yaml_typename = self._yaml_typenames[typ]
        actual_yaml_typename = self._yaml_typenames[type(struct)]
        if not isinstance(struct, typ):
            err = []
            if path:
                err.append('Source file {p}:'.format(p=path[0]))
                err.append('  Problem in: ' + ' -> '.join(['(top level)'] + path[1:] + [name]))
            err.append('"{n}" has to be Yaml {w}, not {a}.'.format(n=name,
                                                                   w=wanted_yaml_typename,
                                                                   a=actual_yaml_typename))
            raise exceptions.YamlTypeError('\n'.join(err))
