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
            for dirname, subdirs, files in os.walk(d):
                yaml_files.extend(map(lambda x: os.path.join(dirname, x), filter(lambda x: x.endswith('.yaml'), files)))

        for f in yaml_files:
            with open(f, 'r') as stream:
                loaded_yamls[f] = yaml.load(stream)

        return loaded_yamls
