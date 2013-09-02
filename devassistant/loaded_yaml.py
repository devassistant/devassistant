import os

from devassistant import settings

class LoadedYaml(object):
    @property
    def load_path(self):
        lp = ''
        for d in settings.DATA_DIRECTORIES:
            if d == os.path.commonprefix([self.path, d]): break

        return d

    @property
    def default_template_dir(self):
        return os.path.join(self.load_path, 'templates')
