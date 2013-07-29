import os
import yaml

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
                loaded_yamls[f] = yaml.load(stream)

        return loaded_yamls

    @classmethod
    def load_yaml(cls, directories, name):
        """Load a yaml file with specified name if found in given directories

        Args:
            directories: list of directories to search
            name: name of the yaml file to load (".yaml" is appended by this method)
        Returns:
            dict with one key/value: {fullpath: loaded yaml structure} (or empty if not found)
        """
        ret = {}
        name_dot_yaml = name + '.yaml'
        for d in directories:
            if d.startswith('/home') and not os.path.exists(d):
                os.makedirs(d)
            for dirname, subdirs, files in os.walk(d):
                if name_dot_yaml in files:
                    path = os.path.join(dirname, name_dot_yaml)
                    ret[path] = yaml.load(open(path, 'r'))
        return ret
