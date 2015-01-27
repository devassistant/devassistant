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
from devassistant.logger import logger
from devassistant import utils
from six.moves import urllib
import logging
import hashlib
try:
    from yaml import CLoader as Loader
except:
    from yaml import Loader
from devassistant.settings import DAPI_API_URL
from devassistant.settings import DATA_DIRECTORIES
from devassistant.settings import DEVASSISTANT_HOME


def _api_url():
    return DAPI_API_URL


def _install_path():
    return DEVASSISTANT_HOME


def _data_dirs():
    return DATA_DIRECTORIES


def _process_req_txt(req):
    '''Returns a processed request or raises an exception'''
    if req.status_code == 404:
        return ''
    if req.status_code != 200:
        raise Exception('Response of the server was {code}'.format(code=req.status_code))
    return req.text


def _process_req(req):
    '''Returns a YAML decoded request'''
    return yaml.load(_process_req_txt(req))


def data(link):
    '''Returns a dictionary from requested link'''
    req = requests.get(link)
    return _process_req(req)


def _unpaginated(what):
    '''Returns a dictionary with all <what>, unpaginated'''
    page = data(_api_url() + what)
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
    return data(_api_url() + 'users/' + username + '/')


def metadap(name):
    '''Returns a dictionary with all info about a given metadap'''
    return data(_api_url() + 'metadaps/' + name + '/')


def dap(name, version=''):
    '''Returns a dictionary with all info about a given dap'''
    if version:
        name += '-' + version
    return data(_api_url() + 'daps/' + name + '/')


def search(query):
    '''Returns a dictionary with the search results'''
    return _unpaginated('search/?q=' + query)


def _print_dap_with_description(mdap):
    print(mdap['package_name'], end='')
    latest = mdap['latest_stable'] or mdap['latest']
    if latest:
        latest = data(latest)
        print(' - ', end='')
        print(latest['summary'], end='')
    print('')


def print_users():
    '''Prints a list of users available on Dapi'''
    u = users()
    count = u['count']
    if not count:
        raise Exception('Could not find any users on DAPI.')
    for user in u['results']:
        print(user['username'], end='')
        if user['full_name']:
            print(' (' + user['full_name'] + ')')
        else:
            print('')


def print_daps():
    '''Prints a list of metadaps available on Dapi'''
    m = metadaps()
    if not m['count']:
        print('Could not find any daps')
        return
    for mdap in m['results']:
        _print_dap_with_description(mdap)


def _get_metadap_dap(name, version=''):
    '''Return data for dap of given or latets version.'''
    m = metadap(name)
    if not m:
        raise Exception('DAP {dap} not found.'.format(dap=name))
    if not version:
        d = m['latest_stable'] or m['latest']
        if d:
            d = data(d)
    else:
        d = dap(name, version)
        if not d:
            raise Exception(
                'DAP {dap} doesn\'t have version {version}.'.format(dap=name, version=version))
    return m, d


def print_dap(name, version=''):
    '''Prints detail for a particular dap'''
    m, d = _get_metadap_dap(name, version)
    if d:
        _name = m['package_name'] + '-' + d['version']
    else:
        _name = m['package_name']
    print(_name)
    for i in range(0, len(_name)):
        print('=', end='')
    print('\n')
    if d:
        print(d['summary'])
        if d['description']:
            print('')
            print(d['description'])
    else:
        print('{dap} has no versions\n'.format(dap=name))
    for item in 'active average_rank rank_count reports'.split():
        print(item, end=': ')
        print(m[item])
    if d:
        for item in 'license homepage bugreports is_pre is_latest is_latest_stable'.split():
            if (d[item] is not None):
                print(item, end=': ')
                print(d[item])


def print_search(query):
    '''Prints the results of a search'''
    m = search(query)
    count = m['count']
    if not count:
        raise Exception('Could not find any DAP packages for your query.')
        return
    for mdap in m['results']:
        mdap = mdap['content_object']
        _print_dap_with_description(mdap)


def get_installed_daps(location=None):
    '''Returns a set of all installed daps
    Either in the given location or in all of them'''
    if location:
        locations = [location]
    else:
        locations = _data_dirs()
    s = set()
    for loc in locations:
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


def uninstall_dap(name, confirm=False, allpaths=False):
    if allpaths:
        location = None
        hint = 'DEVASSISTANT_PATH'
    else:
        location = _install_path()
        hint = utils.unexpanduser(_install_path())
    if name not in get_installed_daps(location=location):
        raise Exception(
            'Cannot uninstall DAP {dap}, it is not in {path}'.
            format(dap=name, path=hint))
    ret = []
    for dap in get_installed_daps(location=location):
        deps = _get_dependencies_of(dap, location=location)
        if deps:
            deps = [_strip_version_from_dependency(dep) for dep in deps]
            if name in deps:
                # this might have changed
                if dap in get_installed_daps(location=location):
                    ret += uninstall_dap(dap, confirm=confirm, allpaths=allpaths)
    if allpaths:
        locations = _data_dirs()
    else:
        locations = [_install_path()]
    for location in locations:
        if name not in get_installed_daps(location=location):
            continue
        g = ['{d}/meta/{dap}.yaml'.format(d=location, dap=name)]
        for loc in 'assistants files icons'.split():
            g += glob.glob('{d}/{loc}/*/{dap}.*'.format(d=location, loc=loc, dap=name))
            g += glob.glob('{d}/{loc}/*/{dap}'.format(d=location, loc=loc, dap=name))
        for loc in 'snippets doc'.split():
            g += glob.glob('{d}/{loc}/{dap}.yaml'.format(d=location, loc=loc, dap=name))
            g += glob.glob('{d}/{loc}/{dap}'.format(d=location, loc=loc, dap=name))
        if confirm:
            print('DAP {name} and the following files and directories will be removed:'.
                  format(name=name))
            for f in g:
                print('    ' + f)
            inp = raw_input if not six.PY3 else input
            ok = inp('Is that OK? [y/N] ')
            if ok.lower() != 'y':
                raise Exception('Stopped by user')
        for f in g:
            try:
                os.remove(f)
            except OSError as e:
                if e.errno == errno.EISDIR:  # Is a directory
                    shutil.rmtree(f)
                elif e.errno == errno.EACCES:  # Permission denied
                    raise Exception('Permission denied, you might want to run this command as root')
                else:
                    raise(e)
    return ret + [name]


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
        raise Exception('DAP {dap} has no version to download.'.format(dap=name))
    filename = url.split('/')[-1]
    path = os.path.join(_dir, filename)
    urllib.request.urlretrieve(url, path)
    dapisum = d['sha256sum']
    downloadedsum = hashlib.sha256(open(path, 'rb').read()).hexdigest()
    if dapisum != downloadedsum:
        os.remove(path)
        raise Exception(
            'DAP {dap} has incorrect sha256sum (DAPI: {dapi}, downloaded: {downloaded})'.
            format(dap=name, dapi=dapisum, downloaded=downloadedsum))
    return path, not bool(directory)


def install_dap_from_path(path, update=False, first=True, force=False, nodeps=False):
    '''Installs a dap from a given path'''
    will_uninstall = False
    dap_obj = dapi.Dap(path)
    if dap_obj.meta['package_name'] in get_installed_daps():
        if not update:
            raise Exception('Won\'t override already installed DAP.')
        else:
            will_uninstall = True
    if os.path.isfile(_install_path()):
        raise Exception(
            '{i} is a file, not a directory.'.format(i=_install_path()))

    _dir = tempfile.mkdtemp()
    old_level = logger.getEffectiveLevel()
    logger.setLevel(logging.ERROR)
    ok = dap_obj.check()
    logger.setLevel(old_level)
    if not ok:
        raise Exception('The DAP you want to install has errors, not installing.')

    installed = []
    if first:
        if not force and not _is_supported_here(dap_obj.meta):
            raise Exception(
                '{0} is not supported on this platform (use --force to suppress this check)'.
                format(dap_obj.meta['package_name']))
        deps = set()
        if not nodeps:
            for dep in dap_obj.meta['dependencies']:
                dep = _strip_version_from_dependency(dep)
                if dep not in get_installed_daps():
                    deps |= _get_all_dependencies_of(dep, force=force)
            for dep in deps:
                if dep not in get_installed_daps():
                    installed += install_dap(dep, first=False)

    dap_obj.extract(_dir)
    if will_uninstall:
        uninstall_dap(dap_obj.meta['package_name'])
    _dapdir = os.path.join(_dir, dap_obj.meta['package_name'] + '-' + dap_obj.meta['version'])
    if not os.path.isdir(_install_path()):
        os.makedirs(_install_path())
    os.mkdir(os.path.join(_dapdir, 'meta'))
    os.rename(os.path.join(_dapdir, 'meta.yaml'),
        os.path.join(_dapdir, 'meta', dap_obj.meta['package_name'] + '.yaml'))
    for f in glob.glob(_dapdir + '/*'):
        dst = os.path.join(_install_path(), os.path.basename(f))
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

    return [dap_obj.meta['package_name']] + installed

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
        with open(meta) as f:
            data = yaml.load(f.read(), Loader=Loader)
        return data['version']
    return None

def _is_supported_here(dap_api_data):
    supported = dap_api_data.get('supported_platforms',[])
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
        with open(meta) as f:
            data = yaml.load(f.read(), Loader=Loader)
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
        # we can do the following not to resolve the dependencies of already installed daps
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
        raise Exception(
            '{0} is not supported on this platform (use --force to suppress this check).'.
            format(name))
    return d.get('dependencies', [])

def install_dap(name, version='', update=False, first=True, force=False, nodeps=False):
    '''Install a dap from dapi
    If update is True, it will remove previously installed daps of the same name'''
    m, d = _get_metadap_dap(name, version)
    if update:
        available = d['version']
        current = get_installed_version_of(name)
        if not current:
            raise Exception('Cannot update not yet installed DAP.')
        if dapver.compare(available, current) <= 0:
            return []
    path, remove_dir = download_dap(name, d=d)

    ret = install_dap_from_path(path, update=update, first=first, force=force, nodeps=nodeps)

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
