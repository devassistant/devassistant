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

        """
            Add assistants in directory /usr/local/share/devassistant
            which can be added by administrator account
        """
        directories.extend([os.path.join('/usr/local/share', 'devassistant')])
        """
            Add assistants in home directory ~/.devassistant
            User can add assistants into that directory
        """
        home_devassistant = os.path.join(os.path.expanduser('~'), '.devassistant')
        if not os.path.exists(home_devassistant):
            os.makedirs(home_devassistant)
        directories.extend([home_devassistant])
        for d in directories:
            for dirname, subdirs, files in os.walk(d):
                yaml_files.extend(map(lambda x: os.path.join(dirname, x), filter(lambda x: x.endswith('.yaml'), files)))

        for f in yaml_files:
            with open(f, 'r') as stream:
                loaded_yamls[f] = yaml.load(stream)

        return loaded_yamls
