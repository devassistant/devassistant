import os
import sys
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


class DapInvalid(Exception):
    '''Exception that indicates invalid dap'''
    pass


class Dap(object):
    '''Class representing a dap

    Everything should be considered read-only. If not, things might blow up.'''
    def __init__(self, dapfile):
        '''Constructor, takes dap file location as argument.
        Loads the dap if at least somehow valid'''
        self.basename = os.path.basename(dapfile)
        try:
            self._tar = tarfile.open(dapfile, mode='r:gz')
        except tarfile.ReadError as e:
            raise DapFileError('%s is not a tar.gz archive'
                               % self.basename)
        except IOError as e:
            raise DapFileError(e)
        metas = set()
        self.files = self._tar.getnames()
        for f in self.files:
            if os.path.basename(f) == 'meta.yaml' \
               and os.path.dirname(f).count('/') == 0:
                metas.add(f)
        if not metas:
            raise DapMetaError('Could not find any meta.yaml in %s'
                               % self.basename)
        if len(metas) > 1:
            raise DapMetaError('Multiple meta.yaml files found in %s (%s)'
                               % (self.basename, ', '.join(metas)))
        self._meta_location = metas.pop()
        self._load_meta(self._get_file(self._meta_location))

    def _get_file(self, path):
        '''Extracts a file from dap to a file-like object'''
        extracted = self._tar.extractfile(path)
        if extracted:
            return extracted
        raise DapFileError('Could not read %s from %s, maybe it\'s a '
                           'directory, bad link or the dap file is corrupted'
                           % (path, self.basename))

    def _load_meta(self, meta):
        '''Load data from meta.yaml to a dictionary'''
        self.meta = yaml.load(meta.read(), Loader=Loader)

    def _report_problem(self, problem):
        '''Report a given problem'''
        if self._check_raises:
            raise DapInvalid(problem)
        if self._check_output:
            self._check_output.write(self.basename + ': ' + problem + '\n')

    def _valid_name(self, name):
        '''TODO: Check if the name is valid'''
        return True

    def _valid_version(self, version):
        '''TODO: Check if the version is valid'''
        return True

    def check(self, network=True, output=sys.stderr, raises=False):
        '''Checks if the dap is valid, reports problems

        Parameters:
            network -- weather to run checks that requires network connection
            output -- where to write() problems, might be None
            raises -- weather to raise an exception immediately after
                      problem is detected'''
        self._check_output = output
        self._check_raises = raises
        problem = self._report_problem

        # Check for required metadata first
        try:
            if not self._valid_name(self.meta['package_name']):
                problem(self.meta['package_name'] + ' is not a valid name')
        except KeyError:
            problem('Package name is not defined (FATAL)')

        try:
            if not self._valid_version(self.meta['version']):
                problem(self.meta['version'] + ' is not a valid version')
        except KeyError:
            problem('Version is not defined')

        # Everything should be in name-version directory
        dirname = os.path.dirname(self._meta_location)
        if not dirname:
            problem('mata.yaml is not in top-level directory')

        del self._check_output
        del self._check_raises
