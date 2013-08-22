import os

import yaml
try:
    from yaml import CLoader as Loader
except:
    from yaml import Loader

from devassistant import settings

class YamlLoader(object):
    @classmethod
    def load_all_yamls(cls, directories):
        """Loads yaml files from all given directories.

        Args:
            directories: list of directories to search
        Returns:
            dict of {fullpath: loaded_yaml_structure}
        """
        yaml_files = []
        loaded_yamls = {}

        for d in directories:
            if d.startswith('/home') and not os.path.exists(d):
                os.makedirs(d)
            for dirname, subdirs, files in os.walk(d):
                yaml_files.extend(map(lambda x: os.path.join(dirname, x), filter(lambda x: x.endswith('.yaml'), files)))

        for f in yaml_files:
            with open(f, 'r') as stream:
                loaded_yamls[f] = yaml.load(stream, Loader=Loader)

        return loaded_yamls

    @classmethod
    def load_yaml(cls, directories, name):
        """Load a yaml file with specified name if found in given directories

        Args:
            directories: list of directories to search
            name: name of the yaml file to load (".yaml" is appended by this method)
        Returns:
            tuple (fullpath, loaded yaml structure) or None if not found
        """
        ret = None
        name_dot_yaml = name if name.endswith('.yaml') else name + '.yaml'
        for d in directories:
            if d.startswith(os.path.expanduser('~')) and not os.path.exists(d):
                os.makedirs(d)
            for dirname, subdirs, files in os.walk(d):
                if name_dot_yaml in files:
                    path = os.path.join(dirname, name_dot_yaml)
                    ret = (path, yaml.load(open(path, 'r'), Loader=Loader))
        return ret

    @classmethod
    def load_yaml_by_path(cls, path):
        """Load a yaml file that is at given path"""
        return yaml.load(open(path, 'r'), Loader=Loader)

    @classmethod
    def _default_template_dir_for(cls, source):
        # both yaml_assistant_loader and yaml_snippet_loader use this, so
        # it seems that there is no other place to put this
        # (although it feels a little weird here)
        base_path = ''
        for d in settings.DATA_DIRECTORIES:
            base_path = os.path.commonprefix([source, d])
            if base_path: break
        return os.path.join(base_path, 'templates')
