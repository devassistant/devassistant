import os

from devassistant import settings


class LoadedYaml(object):
    @property
    def load_path(self):
        for d in settings.DATA_DIRECTORIES:
            if d == os.path.commonprefix([self.path, d]):
                break

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
