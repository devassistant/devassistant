import os
import sys
import tarfile
import yaml
import re
try:
    from yaml import CLoader as Loader
except:
    from yaml import Loader
from . import licenses


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

    _required_meta = set('package_name version license authors summary'.split())
    _optional_meta = set('homepage bugreports description'.split())
    _array_meta = set('authors'.split())

    _url_pattern = r'^(http|https|ftp)\://([a-zA-Z0-9\.\-]+(\:[a-zA-Z0-9\.&%\$\-]+)*@)*' \
                   r'(([a-zA-Z0-9\-]+\.)*[a-zA-Z0-9\-]+\.(museum|[a-z]{2,4}))' \
                   r'(\:[0-9]+)*(/($|[a-zA-Z0-9\.\,\?\'\\\+&%\$#\=~_\-]+))*$'
    _email_pattern = r'[^@]+(@|_at_)([a-zA-Z0-9\-]+\.)*[a-zA-Z0-9\-]+\.(museum|[a-z]{2,4})'

    _meta_valid = {'package_name': re.compile(r'^([a-z][a-z0-9\-_]*[a-z0-9]|[a-z])$'),
                   'version': re.compile(r'^([0-9]|[1-9][0-9]*)(\.([0-9]|[1-9][0-9]*))*(dev|a|b)?$'),
                   'license': licenses,
                   'summary': re.compile(r'^[^\n]+$'),
                   'homepage': re.compile(_url_pattern),
                   'bugreports': re.compile(r'^(' + _email_pattern + '|' + _url_pattern + ')$'),
                   'description': re.compile(r'.+'),
                   'authors': re.compile(r'^(\w+[\w \.]*[\w\.-]+|\w)( +<' + _email_pattern + '>)?$', re.UNICODE)}

    def __init__(self, dapfile, fake=False):
        '''Constructor, takes dap file location as argument.
        Loads the dap if at least somehow valid.
        If fake is True, it fill not open any files, but creates a fake dap'''
        if fake:
            self.basename = 'fake.dap'
            self.files = []
            self.meta = {}
            return

        self.basename = os.path.basename(dapfile)
        try:
            self._tar = tarfile.open(dapfile, mode='r:gz')
        except tarfile.ReadError as e:
            raise DapFileError('%s is not a tar.gz archive' % self.basename)
        except IOError as e:
            raise DapFileError(e)
        metas = set()
        self.files = self._tar.getnames()
        for f in self.files:
            if os.path.basename(f) == 'meta.yaml' and os.path.dirname(f).count('/') == 0:
                metas.add(f)
        if not metas:
            raise DapMetaError('Could not find any meta.yaml in %s' % self.basename)
        if len(metas) > 1:
            raise DapMetaError('Multiple meta.yaml files found in %s (%s)' % (self.basename, ', '.join(metas)))
        self._meta_location = metas.pop()
        self._load_meta(self._get_file(self._meta_location))

    def _get_file(self, path):
        '''Extracts a file from dap to a file-like object'''
        extracted = self._tar.extractfile(path)
        if extracted:
            return extracted
        raise DapFileError('Could not read %s from %s, maybe it\'s a directory, bad link or the dap file is corrupted' % (path, self.basename))

    def _load_meta(self, meta):
        '''Load data from meta.yaml to a dictionary'''
        self.meta = yaml.load(meta.read(), Loader=Loader)

    def _report_problem(self, problem):
        '''Report a given problem'''
        self._problematic = True
        if self._check_raises:
            raise DapInvalid(problem)
        if self._check_output:
            self._check_output.write(self.basename + ': ' + problem + '\n')

    def _isvalid(self, datatype):
        '''Checks if the given datatype is valid in meta'''
        try:
            return bool(Dap._meta_valid[datatype].match(self.meta[datatype]))
        except KeyError:
            self.meta[datatype] = ''
            return datatype in Dap._optional_meta

    def _arevalid(self, datatype):
        '''Checks if the given datatype is valid in meta (for array-like types)'''
        try:
            if not isinstance(self.meta[datatype], list):
                return False, []
        except KeyError:
            self.meta[datatype] = []
            return datatype in Dap._optional_meta
        if not self.meta[datatype] or len(set(self.meta[datatype])) != len(self.meta[datatype]):
            return False, []
        ret = []
        for item in self.meta[datatype]:
            if not Dap._meta_valid[datatype].match(item):
                ret.append(item)
        return not bool(ret), ret

    def check(self, network=True, output=sys.stderr, raises=False):
        '''Checks if the dap is valid, reports problems

        Parameters:
            network -- weather to run checks that requires network connection
            output -- where to write() problems, might be None
            raises -- weather to raise an exception immediately after problem is detected'''
        self._check_output = output
        self._check_raises = raises
        self._problematic = False
        problem = self._report_problem

        # Check for non array-like metadata
        for datatype in (Dap._required_meta | Dap._optional_meta) - Dap._array_meta:
            if not self._isvalid(datatype):
                problem(datatype + ' is not valid')

        # Check for the array-like metadata
        for datatype in Dap._array_meta:
            ok, bads = self._arevalid(datatype)
            if not ok:
                if not bad:
                    problem(datatype + ' is not a valid non-empty list without duplicites')
                else:
                    for bad in bads:
                        problem(bad + ' in ' + datatype + ' is not valid')

        # Everything should be in name-version directory
        dirname = os.path.dirname(self._meta_location)
        if not dirname:
            problem('mata.yaml is not in top-level directory')

        del self._check_output
        del self._check_raises
        return self._problematic
