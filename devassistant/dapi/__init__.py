from __future__ import print_function

import os
import tarfile
import yaml
import re
import logging
import hashlib
import random
try:
    from yaml import CLoader as Loader
except:
    from yaml import Loader
from . import licenses, platforms
from devassistant import yaml_checker
from devassistant.yaml_loader import YamlLoader
from devassistant.exceptions import DapFileError, DapMetaError, DapInvalid, YamlError
from devassistant.logger import logger
from devassistant.utils import strip_prefix, strip_suffix, exc_as_decoded_string


class DapProblem(object):
    '''Class denoting a problem with a DAP'''

    def __init__(self, message, level=logging.ERROR):
        self.message = message
        self.level = level


class DapFormatter(object):
    '''Formatter for different output information for the Dap class'''

    _nice_strings = {# DAP-related
                     'bugreports': 'Issues',
                     'homepage': 'Home page',
                     'license': 'License',

                     # DAPI-related
                     'active': 'DAP Active',
                     'is_pre': 'Pre-release',
                     'is_latest': 'Latest version',
                     'is_latest_stable': 'Latest stable',
                     'average_rank': 'User rating',
                     'reports': 'Reports',
                     }

    @classmethod
    def _format_field(cls, field):
        if isinstance(field, bool):
            return 'Yes' if field else 'No'
        elif field is None:
            return 'Not available'
        else:
            return str(field)

    @classmethod
    def calculate_offset(cls, labels):
        '''Return the maximum length of the provided strings that have a nice
        variant in DapFormatter._nice_strings'''
        used_strings = set(cls._nice_strings.keys()) & set(labels)
        return max([len(cls._nice_strings[s]) for s in used_strings])

    @classmethod
    def format_dapi_score(cls, meta, offset):
        '''Format the line with DAPI user rating and number of votes'''
        if 'average_rank' and 'rank_count' in meta:
            label = (cls._nice_strings['average_rank'] + ':').ljust(offset + 2)
            score = cls._format_field(meta['average_rank'])
            votes = ' ({num} votes)'.format(num=meta['rank_count'])
            return label + score + votes
        else:
            return ''

    @classmethod
    def format_meta_lines(cls, meta, labels, offset, **kwargs):
        '''Return all information from a given meta dictionary in a list of lines'''
        lines = []

        # Name and underline
        name = meta['package_name']
        if 'version' in meta:
            name += '-' + meta['version']
        if 'custom_location' in kwargs:
            name += ' ({loc})'.format(loc=kwargs['custom_location'])

        lines.append(name)
        lines.append(len(name)*'=')
        lines.append('')

        # Summary
        lines.extend(meta['summary'].splitlines())
        lines.append('')

        # Description
        if meta.get('description', ''):
            lines.extend(meta['description'].splitlines())
            lines.append('')


        # Other metadata
        data = []
        for item in labels:
            if meta.get(item, '') != '': # We want to process False and 0
                label = (cls._nice_strings[item] + ':').ljust(offset + 2)
                data.append(label + cls._format_field(meta[item]))

        lines.extend(data)

        return lines

    @classmethod
    def _format_files(cls, files, kind):
        '''Format the list of files (e. g. assistants or snippets'''
        lines = []
        if files:
            lines.append('The following {kind} are contained in this DAP:'.format(kind=kind.title()))
            for f in files:
                lines.append('* ' + strip_prefix(f, kind).replace(os.path.sep, ' ').strip())
            return lines
        else:
            return ['No {kind} are contained in this DAP'.format(kind=kind.title())]

    @classmethod
    def format_assistants_lines(cls, assistants):
        '''Return formatted assistants from the given list in human readable form.'''
        lines = cls._format_files(assistants, 'assistants')

        # Assistant help
        if assistants:
            lines.append('')
            assistant = strip_prefix(random.choice(assistants), 'assistants').replace(os.path.sep, ' ').strip()
            if len(assistants) == 1:
                strings = ['After you install this DAP, you can find help about the Assistant',
                           'by running "da {a} -h" .']
            else:
                strings = ['After you install this DAP, you can find help, for example about the Assistant',
                           '"{a}", by running "da {a} -h".']
            lines.extend([l.format(a=assistant) for l in strings])

        return lines

    @classmethod
    def format_snippets(cls, assistants):
        '''Return formatted snippets from the given list in human readable form.'''
        return cls._format_files(assistants, 'snippets')

    @classmethod
    def format_platforms(cls, platforms):
        '''Formats supported platforms in human readable form'''
        lines = []
        if platforms:
            lines.append('This DAP is only supported on the following platforms:')
            lines.extend([' * ' + platform for platform in platforms])
        return lines

class DapChecker(object):
    '''Class checking a DAP'''

    @classmethod
    def check(cls, dap, network=False, yamls=True, raises=False, logger=logger):
        '''Checks if the dap is valid, reports problems

        Parameters:
            network -- whether to run checks that requires network connection
            output -- where to write() problems, might be None
            raises -- whether to raise an exception immediately after problem is detected'''
        dap._check_raises = raises
        dap._problematic = False
        dap._logger = logger
        problems = list()

        problems += cls.check_meta(dap)
        problems += cls.check_no_self_dependency(dap)
        problems += cls.check_topdir(dap)
        problems += cls.check_files(dap)

        if yamls:
            problems += cls.check_yamls(dap)

        if network:
            problems += cls.check_name_not_on_dapi(dap)

        for problem in problems:
            dap._report_problem(problem.message, problem.level)

        del dap._check_raises
        return not dap._problematic

    @classmethod
    def check_meta(cls, dap):
        '''Check the meta.yaml in the dap.

        Return a list of DapProblems.'''
        problems = list()

        # Check for non array-like metadata
        for datatype in (Dap._required_meta | Dap._optional_meta) - Dap._array_meta:
            if not dap._isvalid(datatype):
                msg = datatype + ' is not valid (or required and unspecified)'
                problems.append(DapProblem(msg))

        # Check for the array-like metadata
        for datatype in Dap._array_meta:
            ok, bads = dap._arevalid(datatype)
            if not ok:
                if not bads:
                    msg = datatype + ' is not a valid non-empty list'
                    problems.append(DapProblem(msg))
                else:
                    for bad in bads:
                        msg = bad + ' in ' + datatype + ' is not valid or is a duplicate'
                        problems.append(DapProblem(msg))

        # Check that there is no unknown metadata
        leftovers = set(dap.meta.keys()) - (Dap._required_meta | Dap._optional_meta)
        if leftovers:
            msg = 'Unknown metadata: ' + str(leftovers)
            problems.append(DapProblem(msg))

        # Check that package_name is not longer than 200 characters
        if len(dap.meta.get('package_name', '')) > 200:
            msg = 'Package name is too long. It must not exceed 200 characters.'
            problems.append(DapProblem(msg))

        return problems

    @classmethod
    def check_topdir(cls, dap):
        '''Check that everything is in the correct top-level directory.

        Return a list of DapProblems'''
        problems = list()
        dirname = os.path.dirname(dap._meta_location)

        if not dirname:
            msg = 'meta.yaml is not in top-level directory'
            problems.append(DapProblem(msg))

        else:
            for path in dap.files:
                if not path.startswith(dirname):
                    msg = path + ' is outside of ' + dirname + ' top-level directory'
                    problems.append(DapProblem(msg))

        if dap.meta['package_name'] and dap.meta['version']:
            desired_dirname = dap._dirname()
            desired_filename = desired_dirname + '.dap'

            if dirname and dirname != desired_dirname:
                msg = 'Top-level directory with meta.yaml is not named ' + desired_dirname
                problems.append(DapProblem(msg))

            if dap.basename != desired_filename:
                msg = 'The dap filename is not ' + desired_filename
                problems.append(DapProblem(msg))

        return problems

    @classmethod
    def check_no_self_dependency(cls, dap):
        '''Check that the package does not depend on itself.

        Return a list of problems.'''
        problems = list()

        if 'package_name' in dap.meta and 'dependencies' in dap.meta:
            dependencies = set()

            for dependency in dap.meta['dependencies']:
                if 'dependencies' in dap._badmeta and dependency in dap._badmeta['dependencies']:
                    continue

                # No version specified
                if not re.search(r'[<=>]', dependency):
                    dependencies.add(dependency)

                # Version specified
                for mark in ['==', '>=', '<=', '<', '>']:
                    dep = dependency.split(mark)
                    if len(dep) == 2:
                        dependencies.add(dep[0].strip())
                        break

            if dap.meta['package_name'] in dependencies:
                msg = 'Depends on dap with the same name as itself'
                problems.append(DapProblem(msg))

        return problems

    @classmethod
    def check_name_not_on_dapi(cls, dap):
        '''Check that the package_name is not registered on Dapi.

        Return list of problems.'''
        problems = list()

        if dap.meta['package_name']:
            from . import dapicli
            d = dapicli.metadap(dap.meta['package_name'])
            if d:
                problems.append(DapProblem('This dap name is already registered on Dapi',
                                           level=logging.WARNING))
        return problems

    @classmethod
    def check_files(cls, dap):
        '''Check that there are only those files the standard accepts.

        Return list of DapProblems.'''
        problems = list()
        dirname = os.path.dirname(dap._meta_location)

        if dirname:
            dirname += '/'
        files = [f for f in dap.files if f.startswith(dirname)]
        if len(files) == 1:
            msg = 'Only meta.yaml in dap'
            problems.append(DapProblem(msg, level=logging.WARNING))
            return problems

        files.remove(dirname + 'meta.yaml')

        # Report and remove empty directories until no more are found
        emptydirs = dap._get_emptydirs(files)
        while emptydirs:
            for ed in emptydirs:
                msg = ed + ' is empty directory (may be nested)'
                problems.append(DapProblem(msg, logging.WARNING))
                files.remove(ed)
            emptydirs = dap._get_emptydirs(files)

        if dap.meta['package_name']:
            name = dap.meta['package_name']

            dirs = re.compile('^' + dirname + '((assistants(/(crt|twk|prep|extra))?|snippets)(/' +
                              name + ')?|icons(/(crt|twk|prep|extra|snippets)(/' + name +
                              ')?)?|files|(files/(crt|twk|prep|extra|snippets)|doc)(/' + name +
                              '(/.+)?)?)$')
            regs = re.compile('^' + dirname + '((assistants(/(crt|twk|prep|extra))|snippets)/' +
                              name + r'(/[^/]+)?\.yaml|icons/(crt|twk|prep|extra|snippets)/' +
                              name + r'(/[^/]+)?\.(' + Dap._icons_ext +
                              ')|(files/(crt|twk|prep|extra|snippets)|doc)/' + name + '/.+)$')

            to_remove = []
            for f in files:
                if dap._is_dir(f) and not dirs.match(f):
                    msg = f + '/ is not allowed directory'
                    problems.append(DapProblem(msg))
                    to_remove.append(f)
                elif not dap._is_dir(f) and not regs.match(f):
                    msg = f + ' is not allowed file'
                    problems.append(DapProblem(msg))
                    to_remove.append(f)
            for r in to_remove:
                files.remove(r)

            # Subdir yamls need a chief
            for directory in ['assistants/' + t for t in 'crt twk prep extra'.split()] + \
                    ['snippets']:
                prefix = dirname + directory + '/'
                for f in files:
                    if f.startswith(prefix) and dap._is_dir(f) and f + '.yaml' not in files:
                        msg = f + '/ present, but ' + f + '.yaml missing'
                        problems.append(DapProblem(msg))

        # Missing assistants and/or snippets
        if not dap.assistants_and_snippets:
            msg = 'No Assistants or Snippets found'
            problems.append(DapProblem(msg, level=logging.WARNING))

        # Icons
        icons = [dap._strip_leading_dirname(i) for i in dap.icons(strip_ext=True)] # we need to report duplicates
        assistants = set([dap._strip_leading_dirname(a) for a in dap.assistants])  # duplicates are fine here

        duplicates = set([i for i in icons if icons.count(i) > 1])
        for d in duplicates:
            msg = 'Duplicate icon for ' + f
            problems.append(DapProblem(msg, level=logging.WARNING))

        icons = set(icons)
        for i in icons - assistants:
            msg = 'Useless icon for non-exisiting assistant ' + i
            problems.append(DapProblem(msg, level=logging.WARNING))

        for a in assistants - icons:
            msg = 'Missing icon for assistant ' + a
            problems.append(DapProblem(msg, level=logging.WARNING))

        # Source files
        for f in cls._get_files_without_assistants(dap, dirname, files):
            msg = 'Useless files for non-exisiting assistant ' + f
            problems.append(DapProblem(msg, level=logging.WARNING))

        return problems

    @classmethod
    def check_yamls(cls, dap):
        '''Check that all assistants and snippets are valid.

        Return list of DapProblems.'''
        problems = list()

        for yaml in dap.assistants_and_snippets:
            path = yaml + '.yaml'
            parsed_yaml = YamlLoader.load_yaml_by_path(dap._get_file(path, prepend=True))
            if parsed_yaml:
                try:
                    yaml_checker.check(path, parsed_yaml)
                except YamlError as e:
                    problems.append(DapProblem(exc_as_decoded_string(e), level=logging.ERROR))
            else:
                problems.append(DapProblem('Empty YAML ' + path, level=logging.WARNING))

        return problems

    @classmethod
    def _get_files_without_assistants(cls, dap, dirname, files):
        folders = set()
        assistants = set()
        assistant_dirs = set(['crt', 'twk', 'prep', 'extra'])

        for f in files:
            # Directories
            if dap._is_dir(f):
                prefix = os.path.join(dirname, 'files', '')
                if f.startswith(prefix):
                    remainder = strip_prefix(f, prefix) # crt/foo/bar/baz
                    name = os.path.join(*remainder.split(os.path.sep)[:2]) # crt/foo
                    folders.add(name)
            else:
                # Assistants
                prefix = os.path.join(dirname, 'assistants', '')
                remainder = strip_prefix(f, prefix)
                for kind in assistant_dirs:
                    if remainder.startswith(kind + os.path.sep):
                        name = strip_suffix(remainder, '.yaml')
                        assistants.add(name)

                # Snippets
                prefix = os.path.join(dirname, 'snippets', '')
                if f.startswith(prefix):
                    name = strip_suffix(strip_prefix(f, dirname + os.path.sep), '.yaml')
                    assistants.add(name)

        return list(folders - assistant_dirs - set(('snippets',)) - assistants)


class Dap(object):
    '''Class representing a dap

    Everything should be considered read-only. If not, things might blow up.'''


    _required_meta = set('package_name version license authors summary'.split())
    _optional_meta = set('homepage bugreports description dependencies supported_platforms'.
        split())
    _array_meta = set('authors dependencies supported_platforms'.split())

    _url_pattern = r'(http|https|ftp)\://([a-zA-Z0-9\.\-]+(\:[a-zA-Z0-9\.&%\$\-]+)*@)*' \
                   r'(([a-zA-Z0-9\-]+\.)*[a-zA-Z0-9\-]+\.(museum|[a-z]{2,4}))' \
                   r'(\:[0-9]+)*(/($|[a-zA-Z0-9\.\,\?\'\\\+&%\$#\=~_\-]+))*'
    _email_pattern = r'[^@]+(@|_at_)([a-zA-Z0-9\-]+\.)*[a-zA-Z0-9\-]+\.(museum|[a-z]{2,4})'
    _name_pattern = r'([a-z][a-z0-9\-_]*[a-z0-9]|[a-z])'
    _version_pattern = r'([0-9]|[1-9][0-9]*)(\.([0-9]|[1-9][0-9]*))*(dev|a|b)?'

    _assistants_pattern = re.compile(r'assistants/.*\.yaml')
    _snippets_pattern = re.compile(r'snippets/.*\.yaml')
    _icons_ext = 'svg|png'
    _icons_pattern = re.compile(r'icons/.*\.({ext})'.format(ext=_icons_ext))

    _meta_valid = {'package_name': re.compile(r'^' + _name_pattern + r'$'),
                   'version': re.compile(r'^' + _version_pattern + r'$'),
                   'license': licenses,
                   'summary': re.compile(r'^[^\n]+$'),
                   'homepage': re.compile(r'^' + _url_pattern + r'$'),
                   'bugreports': re.compile(r'^(' + _email_pattern + '|' + _url_pattern + ')$'),
                   'description': re.compile(r'.+'),
                   'authors': re.compile(r'^(\w+[\w \.]*[\w\.-]+|\w)( +<' + _email_pattern +
                       '>)?$', re.UNICODE),
                   'dependencies': re.compile(r'^' + _name_pattern + r'( *(<|>|<=|>=|==) *' +
                       _version_pattern + r')?$'),
                   'supported_platforms': platforms}


    def __init__(self, dapfile, fake=False, mimic_filename=None):
        '''Constructor, takes dap file location as argument.
        Loads the dap if at least somehow valid.
        If fake is True, it fill not open any files, but creates a fake dap'''

        # Basename
        if mimic_filename:
            self.basename = mimic_filename
        elif fake:
            self.basename = 'fake.dap'
        else:
            self.basename = os.path.basename(dapfile)

        # Files
        if fake:
            self.files = []
            self.meta = {}
        else:
            self._tar = self._load_tar(dapfile)
            self.files = sorted(self._tar.getnames())
            self._meta_location = self._get_meta(self.files, self.basename)
            self.meta = self._load_meta(self._get_file(self._meta_location))
            self.sha256sum = hashlib.sha256(open(dapfile, 'rb').read()).hexdigest()

        self._find_bad_meta()

    def _strip_leading_dirname(self, path):
        '''Strip leading directory name from the given path'''
        return os.path.sep.join(path.split(os.path.sep)[1:])

    @property
    def _stripped_files(self):
        '''Get contents of self.files with the root directory stripped'''
        return [self._strip_leading_dirname(f) for f in self.files]

    @property
    def assistants(self):
        '''Get all assistants in this DAP'''
        return [strip_suffix(f, '.yaml') for f in self._stripped_files if self._assistants_pattern.match(f)]

    @property
    def snippets(self):
        '''Get all snippets in this DAP'''
        return [strip_suffix(f, '.yaml') for f in self._stripped_files if self._snippets_pattern.match(f)]

    @property
    def assistants_and_snippets(self):
        '''Get all assistants and snippets in this DAP'''
        return self.assistants + self.snippets

    def icons(self, strip_ext=False):
        '''Get all icons in this DAP, optionally strip extensions'''
        result =  [f for f in self._stripped_files if self._icons_pattern.match(f)]
        if strip_ext:
            result = [strip_suffix(f, '\.({ext})'.format(ext=self._icons_ext), regex=True) for f in result]

        return result

    def _find_bad_meta(self):
        '''Fill self._badmeta with meta datatypes that are invalid'''
        self._badmeta = dict()

        for datatype in self.meta:
            for item in self.meta[datatype]:
                if not Dap._meta_valid[datatype].match(item):
                    if datatype not in self._badmeta:
                        self._badmeta[datatype] = []
                    self._badmeta[datatype].append(item)

    def _load_tar(self, dapfile):
        try:
            return tarfile.open(dapfile, mode='r:gz')
        except tarfile.ReadError as e:
            raise DapFileError('%s is not a tar.gz archive' % self.basename)
        except IOError as e:
            raise DapFileError(e)

    def _get_meta(self, files, basename):
        metas = set()

        for f in files:
            if os.path.basename(f) == 'meta.yaml' and os.path.dirname(f).count('/') == 0:
                metas.add(f)

        if not metas:
            raise DapMetaError('Could not find any meta.yaml in %s' % basename)

        if len(metas) > 1:
            raise DapMetaError('Multiple meta.yaml files found in %s (%s)' %
                (basename, ', '.join(metas)))

        return metas.pop()

    def _dirname(self):
        '''Get root dirname'''
        return self.meta['package_name'] + '-' + self.meta['version']

    def _get_file(self, path, prepend=False):
        '''Extracts a file from dap to a file-like object'''
        if prepend:
            path = os.path.join(self._dirname(), path)
        extracted = self._tar.extractfile(path)
        if extracted:
            return extracted
        raise DapFileError(('Could not read %s from %s, maybe it\'s a directory,' +
            'bad link or the dap file is corrupted') % (path, self.basename))

    def _load_meta(self, meta):
        '''Load data from meta.yaml to a dictionary'''
        meta = yaml.load(meta, Loader=Loader)

        # Versions are often specified in a format that is convertible to an
        # int or a float, so we want to make sure it is interpreted as a str.
        # Fix for the bug #300.
        if 'version' in meta:
            meta['version'] = str(meta['version'])

        return meta

    def _report_problem(self, problem, level=logging.ERROR):
        '''Report a given problem'''
        problem = self.basename + ': ' + problem
        if self._logger.isEnabledFor(level):
            self._problematic = True
        if self._check_raises:
            raise DapInvalid(problem)
        self._logger.log(level, problem)

    def _isvalid(self, datatype):
        '''Checks if the given datatype is valid in meta'''
        if datatype in self.meta:
            return bool(Dap._meta_valid[datatype].match(self.meta[datatype]))
        else:
            return datatype in Dap._optional_meta

    def _arevalid(self, datatype):
        '''Checks if the given datatype is valid in meta (for array-like types)'''
        # Datatype not specified
        if datatype not in self.meta:
            return datatype in Dap._optional_meta, []

        # Required datatype empty
        if datatype in self._required_meta and not self.meta[datatype]:
            return False, []

        # Datatype not a list
        if not isinstance(self.meta[datatype], list):
            return False, []

        # Duplicates found
        duplicates = set([x for x in self.meta[datatype] if self.meta[datatype].count(x) > 1])
        if duplicates:
            return False, list(duplicates)

        if datatype in self._badmeta:
            return False, self._badmeta[datatype]
        else:
            return True, []

        # Checking if all items are valid
        bad = []
        for item in self.meta[datatype]:
            if not Dap._meta_valid[datatype].match(item):
                bad.append(item)
        return len(bad) == 0, bad

    def _is_dir(self, f):
        '''Check if the given in-dap file is a directory'''
        return self._tar.getmember(f).type == tarfile.DIRTYPE

    def _get_emptydirs(self, files):
        '''Find empty directories and return them
        Only works for actual files in dap'''
        emptydirs = []
        for f in files:
            if self._is_dir(f):
                empty = True
                for ff in files:
                    if ff.startswith(f + '/'):
                        empty = False
                        break
                if empty:
                    emptydirs.append(f)
        return emptydirs

    def extract(self, location):
        '''Extract the contents of a dap to a given location'''
        self._tar.extractall(location)
