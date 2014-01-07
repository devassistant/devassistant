import os
import tarfile
import yaml
try:
    from yaml import CLoader as Loader
except:
    from yaml import Loader


class DapFileError(Exception):
    '''Exception that indicates something wrong with dap file'''
    pass


class DapMetaError(Exception):
    '''Exception that indicates something wrong with dap's metadata'''
    pass


class Dap(object):
    '''Class representing a dap'''
    def __init__(self, dapfile):
        '''Constructor, takes dap file location as argument.
        Loads the dap if at least somehow valid'''
        self._dap_basename = os.path.basename(dapfile)
        try:
            self._tar = tarfile.open(dapfile, mode='r:gz')
        except tarfile.ReadError as e:
            raise DapFileError('%s is not a tar.gz archive'
                               % self._dap_basename)
        except IOError as e:
            raise DapFileError(e)
        metas = set()
        for member in self._tar.getmembers():
            if os.path.basename(member.name) == 'meta.yaml' \
               and os.path.dirname(member.name).count('/') == 0:
                metas.add(member.name)
        if not metas:
            raise DapMetaError('Could not find any meta.yaml in %s'
                               % self._dap_basename)
        if len(metas) > 1:
            raise DapMetaError('Multiple meta.yaml files found in %s (%s)'
                               % (self._dap_basename, ', '.join(metas)))
        self._load_meta(self._get_file(metas.pop()))

    def _get_file(self, path):
        '''Extracts a file from dap to a file-like object'''
        extracted = self._tar.extractfile(path)
        if extracted:
            return extracted
        raise DapFileError('Could not read %s from %s, maybe it\'s a '
                           'directory, bad link or the dap file is corrupted'
                           % (path, self._dap_basename))

    def _load_meta(self, meta):
        '''Load data from meta.yaml to a dictionary'''
        self._meta = yaml.load(meta.read(), Loader=Loader)
