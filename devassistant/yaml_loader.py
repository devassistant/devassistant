import os

import yaml
try:
    from yaml import CLoader as Loader
except:
    from yaml import Loader

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
    def load_yaml_by_relpath(cls, directories, rel_path):
        """Load a yaml file with path that is relative to one of given directories.

        Args:
            directories: list of directories to search
            name: relative path of the yaml file to load
        Returns:
            tuple (fullpath, loaded yaml structure) or None if not found
        """
        ret = None
        for d in directories:
            if d.startswith(os.path.expanduser('~')) and not os.path.exists(d):
                os.makedirs(d)
            possible_path = os.path.join(d, rel_path)
            if os.path.exists(possible_path):
                return (possible_path, cls.load_yaml_by_path(possible_path))

        return None

    @classmethod
    def load_yaml_by_path(cls, path):
        """Load a yaml file that is at given path"""
        return yaml.load(open(path, 'r'), Loader=Loader)
