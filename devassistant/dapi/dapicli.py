from __future__ import print_function

import errno
import requests
import yaml
import os
import glob
import shutil
import six
import tempfile
from devassistant import dapi
from devassistant.dapi import dapver
from devassistant.exceptions import DapiCommError, DapiLocalError
from devassistant.logger import logger
from devassistant import lang
from devassistant import utils
from six.moves import urllib
from six.moves.urllib.parse import urlencode
import logging
import hashlib
try:
    from yaml import CLoader as Loader
except:
    from yaml import Loader
from devassistant.settings import DAPI_API_URL
from devassistant.settings import DAPI_API_MIRROR_URL
from devassistant.settings import DATA_DIRECTORIES
from devassistant.settings import DISTRO_DIRECTORY
from devassistant.settings import INSTALL_DIRECTORY


BASIC_LABELS = ['license', 'homepage', 'bugreports']
EXTRA_LABELS = ['is_pre', 'is_latest', 'is_latest_stable', 'reports']

def _api_url(mirror=False):
    if mirror:
        return DAPI_API_MIRROR_URL
    return DAPI_API_URL


def _install_path():
    return INSTALL_DIRECTORY


def _data_dirs():
    return DATA_DIRECTORIES


def _process_req_txt(req):
    '''Returns a processed request or raises an exception'''
    if req.status_code == 404:
        return ''
    if req.status_code != 200:
        raise DapiCommError('Response of the server was {code}'.format(code=req.status_code))
    return req.text


def _process_req(req):
    '''Returns a YAML decoded request'''
    return yaml.load(_process_req_txt(req))


def _get_from_dapi_or_mirror(link):
    '''Tries to get the link form DAPI or the mirror'''
    exception = False
    try:
        req = requests.get(_api_url() + link, timeout=5)
    except requests.exceptions.RequestException:
        exception = True
    attempts = 1

    while exception or str(req.status_code).startswith('5'):
        if attempts > 5:
            raise DapiCommError('Could not connect to the API endpoint, sorry.')
        exception = False
        try:
            # Every second attempt, use the mirror
            req = requests.get(_api_url(attempts % 2) + link, timeout=5*attempts)
        except requests.exceptions.RequestException:
            exception = True
        attempts += 1

    return req


def _remove_api_url_from_link(link):
    '''Remove the API URL from the link if it is there'''
    if link.startswith(_api_url()):
        link = link[len(_api_url()):]
    if link.startswith(_api_url(mirror=True)):
        link = link[len(_api_url(mirror=True)):]
    return link


def data(link):
    '''Returns a dictionary from requested link'''
    link = _remove_api_url_from_link(link)
    req = _get_from_dapi_or_mirror(link)
    return _process_req(req)


def _unpaginated(what):
    '''Returns a dictionary with all <what>, unpaginated'''
    page = data(what)
    results = page['results']
    count = page['count']
    while page['next']:
        page = data(page['next'])
        results += page['results']
        count += page['count']
    return {'results': results, 'count': count}


def users():
    '''Returns a dictionary with all users'''
    return _unpaginated('users')


def metadaps():
    '''Returns a dictionary with all metadaps'''
    return _unpaginated('metadaps')


def daps():
    '''Returns a dictionary with all daps'''
    return _unpaginated('daps')


def user(username=''):
    '''Returns a dictionary with all info about a given user'''
    return data('users/' + username + '/')


def metadap(name):
    '''Returns a dictionary with all info about a given metadap'''
    return data('metadaps/' + name + '/')


def dap(name, version=''):
    '''Returns a dictionary with all info about a given dap'''
    if version:
        name += '-' + version
    return data('daps/' + name + '/')


def search(q, **kwargs):
    '''Returns a dictionary with the search results'''
    data = {'q': q}
    for key, value in kwargs.items():
        if value:
            if type(value) == bool:
                data[key] = 'on'
            else:
                data[key] = value
    return _unpaginated('search/?' + urlencode(data))


def _format_dap_with_description(mdap):
    string = utils.bold(mdap['package_name'])
    latest = mdap['latest_stable'] or mdap['latest']
    if latest:
        latest = data(latest)
        string += ' - ' + latest['summary']
    return [string]


def format_users():
    '''Formats a list of users available on Dapi'''
    lines = []
    u = users()
    count = u['count']
    if not count:
        raise DapiCommError('Could not find any users on DAPI.')
    for user in u['results']:
        line = user['username']
        if user['full_name']:
            line += ' (' + user['full_name'] + ')'
        lines.append(line)
    return lines


def format_daps(simple=False, skip_installed=False):
    '''Formats a list of metadaps available on Dapi'''
    lines= []
    m = metadaps()
    if not m['count']:
        logger.info('Could not find any daps')
        return
    for mdap in sorted(m['results'], key=lambda mdap: mdap['package_name']):
        if skip_installed and mdap['package_name'] in get_installed_daps():
            continue
        if simple:
            logger.info(mdap['package_name'])
        else:
            for line in _format_dap_with_description(mdap):
                lines.append(line)
    return lines


def _get_metadap_dap(name, version=''):
    '''Return data for dap of given or latest version.'''
    m = metadap(name)
    if not m:
        raise DapiCommError('DAP {dap} not found.'.format(dap=name))
    if not version:
        d = m['latest_stable'] or m['latest']
        if d:
            d = data(d)
    else:
        d = dap(name, version)
        if not d:
            raise DapiCommError(
                'DAP {dap} doesn\'t have version {version}.'.format(dap=name, version=version))
    return m, d


def format_dap_from_dapi(name, version='', full=False):
    '''Formats information about given DAP from DAPI in a human readable form to list of lines'''
    lines = []
    m, d = _get_metadap_dap(name, version)

    if d:
        # Determining label width
        labels = BASIC_LABELS + ['average_rank'] # average_rank comes from m, not d
        if full:
            labels.extend(EXTRA_LABELS)
        label_width = dapi.DapFormatter.calculate_offset(labels)

        # Metadata
        lines += dapi.DapFormatter.format_meta_lines(d, labels=labels, offset=label_width)
        lines.append(dapi.DapFormatter.format_dapi_score(m, offset=label_width))

        if 'assistants' in d:
            # Assistants
            assistants = sorted([a for a in d['assistants'] if a.startswith('assistants')])
            lines.append('')
            for line in dapi.DapFormatter.format_assistants_lines(assistants):
                lines.append(line)

            # Snippets
            if full:
                snippets = sorted([a for a in d['assistants'] if a.startswith('snippets')])
                lines.append('')
                lines += dapi.DapFormatter.format_snippets(snippets)

        # Supported platforms
        if d.get('supported_platforms', ''):
            lines.append('')
            lines += dapi.DapFormatter.format_platforms(d['supported_platforms'])

        lines.append('')
    return lines


def format_local_dap(dap, full=False, **kwargs):
    '''Formaqts information about the given local DAP in a human readable form to list of lines'''
    lines = []

    # Determining label width
    label_width = dapi.DapFormatter.calculate_offset(BASIC_LABELS)

    # Metadata
    lines.append(dapi.DapFormatter.format_meta(dap.meta, labels=BASIC_LABELS,
                                               offset=label_width, **kwargs))

    # Assistants
    lines.append('')
    lines.append(dapi.DapFormatter.format_assistants(dap.assistants))

    # Snippets
    if full:
        lines.append('')
        lines.append(dapi.DapFormatter.format_snippets(dap.snippets))

    # Supported platforms
    if 'supported_platforms' in dap.meta:
        lines.append('')
        lines.append(dapi.DapFormatter.format_platforms(dap.meta['supported_platforms']))

    lines.append()
    return lines


def format_installed_dap(name, full=False):
    '''Formats information about an installed DAP in a human readable form to list of lines'''
    dap_data = get_installed_daps_detailed().get(name)
    if not dap_data:
        raise DapiLocalError('DAP "{dap}" is not installed, can not query for info.'.format(dap=name))

    locations = [os.path.join(data['location'], '') for data in dap_data]
    for location in locations:
        dap = dapi.Dap(None, fake=True, mimic_filename=name)
        meta_path = os.path.join(location, 'meta', name + '.yaml')
        with open(meta_path, 'r') as fh:
            dap.meta = dap._load_meta(fh)
        dap.files = _get_assistants_snippets(location, name)
        dap._find_bad_meta()

        format_local_dap(dap, full=full, custom_location=os.path.dirname(location))


def format_installed_dap_list(simple=False):
    '''Formats all installed DAPs in a human readable form to list of lines'''
    lines = []
    if simple:
        for pkg in sorted(get_installed_daps()):
            lines.append(pkg)
    else:
        for pkg, instances in sorted(get_installed_daps_detailed().items()):
            versions = []
            for instance in instances:
                location = utils.unexpanduser(instance['location'])
                version = instance['version']
                if not versions:  # if this is the first
                    version = utils.bold(version)
                versions.append('{v}:{p}'.format(v=version, p=location))
            pkg = utils.bold(pkg)
            lines.append('{pkg} ({versions})'.format(pkg=pkg, versions=' '.join(versions)))
    return lines


def _get_assistants_snippets(path, name):
    '''Get Assistants and Snippets for a given DAP name on a given path'''
    result = []
    subdirs = {'assistants': 2, 'snippets': 1} # Values used for stripping leading path tokens

    for loc in subdirs:
        for root, dirs, files in os.walk(os.path.join(path, loc)):
            for filename in [utils.strip_prefix(os.path.join(root, f), path) for f in files]:
                stripped = os.path.sep.join(filename.split(os.path.sep)[subdirs[loc]:])
                if stripped.startswith(os.path.join(name, '')) or stripped == name + '.yaml':
                    result.append(os.path.join('fakeroot', filename))

    return result


def format_search(q, **kwargs):
    '''Formats the results of a search'''
    m = search(q, **kwargs)
    count = m['count']
    if not count:
        raise DapiCommError('Could not find any DAP packages for your query.')
        return
    for mdap in m['results']:
        mdap = mdap['content_object']
        return _format_dap_with_description(mdap)


def get_installed_daps(location=None, skip_distro=False):
    '''Returns a set of all installed daps
    Either in the given location or in all of them'''
    if location:
        locations = [location]
    else:
        locations = _data_dirs()
    s = set()
    for loc in locations:
        if skip_distro and loc == DISTRO_DIRECTORY:
            continue
        g = glob.glob('{d}/meta/*.yaml'.format(d=loc))
        for meta in g:
            s.add(meta.split('/')[-1][:-len('.yaml')])
    return s


def get_installed_daps_detailed():
    '''Returns a dictionary with all installed daps and their versions and locations
    First version and location in the dap's list is the one that is preferred'''
    daps = {}
    for loc in _data_dirs():
        s = get_installed_daps(loc)
        for dap in s:
            if dap not in daps:
                daps[dap] = []
            daps[dap].append({'version': get_installed_version_of(dap, loc), 'location': loc})
    return daps


def uninstall_dap(name, confirm=False, allpaths=False, __ui__=''):
    if allpaths:
        location = None
        hint = 'DEVASSISTANT_PATH'
    else:
        location = _install_path()
        hint = utils.unexpanduser(_install_path())
    if name not in get_installed_daps(location=location):
        raise DapiLocalError('Cannot uninstall DAP {d}, it is not in {p}'.format(d=name, p=hint))
    ret = []

    # We need to remove all the daps depending on this one
    for dap in get_installed_daps(location=location, skip_distro=True):
        deps = _get_dependencies_of(dap, location=location)
        if deps:
            deps = [_strip_version_from_dependency(dep) for dep in deps]
            if name in deps:
                # This dap might have been removed when removing other dap(s) in this loop
                if dap in get_installed_daps(location=location, skip_distro=True):
                    ret += uninstall_dap(dap, confirm=confirm, allpaths=allpaths, __ui__=__ui__)

    if allpaths:
        locations = _data_dirs()
    else:
        locations = [_install_path()]

    for location in locations:
        if name not in get_installed_daps(location=location):
            continue
        if location == DISTRO_DIRECTORY:
            logger.warn(
                'Skipping {d} in {l}, as it is protected. See docs for explanation.'.format(
                    d=name, l=DISTRO_DIRECTORY))
            continue

        g = ['{d}/meta/{dap}.yaml'.format(d=location, dap=name)]
        for loc in 'assistants files icons'.split():
            g += glob.glob('{d}/{loc}/*/{dap}.*'.format(d=location, loc=loc, dap=name))
            g += glob.glob('{d}/{loc}/*/{dap}'.format(d=location, loc=loc, dap=name))
        for loc in 'snippets doc'.split():
            g += glob.glob('{d}/{loc}/{dap}.yaml'.format(d=location, loc=loc, dap=name))
            g += glob.glob('{d}/{loc}/{dap}'.format(d=location, loc=loc, dap=name))

        if confirm:
            msg = 'DAP {name} and the following files and directories will be removed:\n'
            msg = msg.format(name=name)
            for f in g:
                msg += '    ' + utils.unexpanduser(f) + '\n'

            comm = {'message': msg, 'prompt': 'Is that OK?'}
            command = lang.Command(comm=comm, comm_type='ask_confirm', kwargs={'__ui__': __ui__})
            answer = command.run()[0]
            if not answer:
                raise DapiLocalError('Stopped by user')
        for f in g:
            try:
                os.remove(f)
            except OSError as e:
                if e.errno == errno.EISDIR:  # Is a directory
                    shutil.rmtree(f)
                elif e.errno == errno.EACCES:  # Permission denied
                    raise DapiLocalError(
                        'Permission denied, you might want to run this command as root')
                else:
                    raise(e)
        ret += [name]
    return ret


def download_dap(name, version='', d='', directory=''):
    '''Download a dap to a given or temporary directory
    Return a path to that file together with information if the directory should be later deleted
    '''
    if not d:
        m, d = _get_metadap_dap(name, version)
    if directory:
        _dir = directory
    else:
        _dir = tempfile.mkdtemp()
    try:
        url = d['download']
    except TypeError:
        raise DapiCommError('DAP {dap} has no version to download.'.format(dap=name))
    filename = url.split('/')[-1]
    path = os.path.join(_dir, filename)
    urllib.request.urlretrieve(url, path)
    dapisum = d['sha256sum']
    downloadedsum = hashlib.sha256(open(path, 'rb').read()).hexdigest()
    if dapisum != downloadedsum:
        os.remove(path)
        raise DapiLocalError(
            'DAP {dap} has incorrect sha256sum (DAPI: {dapi}, downloaded: {downloaded})'.
            format(dap=name, dapi=dapisum, downloaded=downloadedsum))
    return path, not bool(directory)


def install_dap_from_path(path, update=False, update_allpaths=False, first=True,
                          force=False, nodeps=False, reinstall=False, __ui__=''):
    '''Installs a dap from a given path'''
    will_uninstall = False
    dap_obj = dapi.Dap(path)
    name = dap_obj.meta['package_name']

    if name in get_installed_daps():
        if not update and not reinstall:
            raise DapiLocalError(
                'DAP {name} is already installed. '
                'Run `da pkg list` to see it\'s location, or use --reinstall to ignore this check.'
                .format(name=name))
        elif not update_allpaths and name in get_installed_daps(_install_path()):
            will_uninstall = True
        elif update_allpaths and name in get_installed_daps():
            will_uninstall = True

    if update and update_allpaths:
        install_locations = []
        for pair in get_installed_daps_detailed()[name]:
            install_locations.append(pair['location'])
    else:
        install_locations = [_install_path()]

    # This should not happen unless someone did it on purpose
    for location in install_locations:
        if os.path.isfile(location):
            raise DapiLocalError(
                '{i} is a file, not a directory.'.format(i=_install_path()))

    _dir = tempfile.mkdtemp()

    old_level = logger.getEffectiveLevel()
    logger.setLevel(logging.ERROR)
    ok = dapi.DapChecker.check(dap_obj)
    logger.setLevel(old_level)

    if not ok:
        raise DapiLocalError('The DAP you want to install has errors, not installing.')

    installed = []
    if first:
        if not force and not _is_supported_here(dap_obj.meta):
            raise DapiLocalError(
                '{0} is not supported on this platform (use --force to suppress this check)'.
                format(name))

        deps = set()
        if 'dependencies' in dap_obj.meta and not nodeps:
            for dep in dap_obj.meta['dependencies']:
                dep = _strip_version_from_dependency(dep)
                if dep not in get_installed_daps():
                    deps |= _get_all_dependencies_of(dep, force=force)
            for dep in deps:
                if dep not in get_installed_daps():
                    installed += install_dap(dep, first=False, __ui__=__ui__)

    dap_obj.extract(_dir)

    if will_uninstall:
        uninstall_dap(name, allpaths=update_allpaths, __ui__=__ui__)

    _dapdir = os.path.join(_dir, name + '-' + dap_obj.meta['version'])

    if not os.path.isdir(_install_path()):
        os.makedirs(_install_path())

    os.mkdir(os.path.join(_dapdir, 'meta'))
    os.rename(os.path.join(_dapdir, 'meta.yaml'),
              os.path.join(_dapdir, 'meta', name + '.yaml'))

    for location in install_locations:
        for f in glob.glob(_dapdir + '/*'):
            dst = os.path.join(location, os.path.basename(f))
            if os.path.isdir(f):
                if not os.path.exists(dst):
                    os.mkdir(dst)
                for src_dir, dirs, files in os.walk(f):
                    dst_dir = src_dir.replace(f, dst)
                    if not os.path.exists(dst_dir):
                        os.mkdir(dst_dir)
                    for file_ in files:
                        src_file = os.path.join(src_dir, file_)
                        dst_file = os.path.join(dst_dir, file_)
                        shutil.copyfile(src_file, dst_file)
            else:
                shutil.copyfile(f, dst)
    try:
        shutil.rmtree(_dir)
    except:
        pass

    return [name] + installed


def _strip_version_from_dependency(dep):
    '''For given dependency string, return only the package name'''
    usedmark = ''
    for mark in '< > ='.split():
        split = dep.split(mark)
        if len(split) > 1:
            usedmark = mark
            break
    if usedmark:
        return split[0].strip()
    else:
        return dep.strip()


def get_installed_version_of(name, location=None):
    '''Gets the installed version of the given dap or None if not installed
    Searches in all dirs by default, otherwise in the given one'''
    if location:
        locations = [location]
    else:
        locations = _data_dirs()

    for loc in locations:
        if name not in get_installed_daps(loc):
            continue
        meta = '{d}/meta/{dap}.yaml'.format(d=loc, dap=name)
        data = yaml.load(open(meta), Loader=Loader)
        return str(data['version'])
    return None


def _is_supported_here(dap_api_data):
    supported = dap_api_data.get('supported_platforms', [])
    if not supported:
        # assume all platforms are supported
        return True
    return utils.get_distro_name() in supported


def _get_dependencies_of(name, location=None):
    '''
    Returns list of first level dependencies of the given installed dap
    or dap from Dapi  if not installed
    If a location is specified, this only checks for dap installed in that path
    and return [] if the dap is not located there
    '''
    if not location:
        detailed_dap_list = get_installed_daps_detailed()
        if name not in detailed_dap_list:
            return _get_api_dependencies_of(name)
        location = detailed_dap_list[name][0]['location']

    meta = '{d}/meta/{dap}.yaml'.format(d=location, dap=name)
    try:
        data = yaml.load(open(meta), Loader=Loader)
    except IOError:
        return []
    return data.get('dependencies', [])


def _get_all_dependencies_of(name, deps=set(), force=False):
    '''Returns list of dependencies of the given dap from Dapi recursively'''
    first_deps = _get_api_dependencies_of(name, force=force)
    for dep in first_deps:
        dep = _strip_version_from_dependency(dep)
        if dep in deps:
            continue
        # we do the following not to resolve the dependencies of already installed daps
        if dap in get_installed_daps():
            continue
        deps |= _get_all_dependencies_of(dep, deps)
    return deps | set([name])


def _get_api_dependencies_of(name, version='', force=False):
    '''Returns list of first level dependencies of the given dap from Dapi'''
    m, d = _get_metadap_dap(name, version=version)
    # We need the dependencies to install the dap,
    # if the dap is unsupported, raise an exception here
    if not force and not _is_supported_here(d):
        raise DapiLocalError(
            '{0} is not supported on this platform (use --force to suppress this check).'.
            format(name))
    return d.get('dependencies', [])


def install_dap(name, version='', update=False, update_allpaths=False, first=True,
                force=False, nodeps=False, reinstall=False, __ui__=''):
    '''Install a dap from dapi
    If update is True, it will remove previously installed daps of the same name'''
    m, d = _get_metadap_dap(name, version)
    if update:
        available = d['version']
        current = get_installed_version_of(name)
        if not current:
            raise DapiLocalError('Cannot update not yet installed DAP.')
        if dapver.compare(available, current) <= 0:
            return []
    path, remove_dir = download_dap(name, d=d)

    ret = install_dap_from_path(path, update=update, update_allpaths=update_allpaths, first=first,
                                force=force, nodeps=nodeps, reinstall=reinstall, __ui__=__ui__)

    try:
        if remove_dir:
            shutil.rmtree(os.dirname(path))
        else:
            os.remove(path)
    except:
        pass

    return ret


def get_dependency_metadata():
    '''Returns list of strings with dependency metadata from Dapi'''
    link = os.path.join(_api_url(), 'meta.txt')
    return _process_req_txt(requests.get(link)).split('\n')
