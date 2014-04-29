from __future__ import print_function

import requests
import yaml
import os
import glob
import shutil
import tempfile
import urllib
import tarfile
import daploader
from sh import mkdir
from sh import cp

DEFAULT_API_URL = 'http://dapi.devassistant.org/api/'
DEFAULT_USER_INSTALL = os.path.expanduser('~/.devassistant')
DEFAULT_ROOT_INSTALL = '/usr/local/share/devassistant'


def _api_url():
    return os.environ.get('DAPI_API_URL', DEFAULT_API_URL)


def _install_path():
    path = os.environ.get('DAPI_INSTALL', None)
    if path:
        if path.endswith('/'):
            return path[:-1]
        return path
    if os.geteuid() == 0:
        return DEFAULT_ROOT_INSTALL
    return DEFAULT_USER_INSTALL


def _process_req(req):
    '''Returns a processed request or raises an exception'''
    if req.status_code == 404:
        return {}
    if req.status_code != 200:
        raise Exception('Response of the server was {code}'.format(code=req.status_code))
    return yaml.load(req.text)


def data(link):
    '''Returns a dictionary from requested link'''
    test = os.environ.get('DAPI_FAKE_DATA', None)
    if test is not None:
        return yaml.load(test)
    req = requests.get(link)
    return _process_req(req)


def _paginated(what, page=''):
    '''Returns a dictionary with all <waht>, paginated'''
    if page:
        page = '?page={page}'.format(page=page)
    return data(_api_url() + what + '/' + page)


def users(page=''):
    '''Returns a dictionary with all users, paginated'''
    return _paginated('users', page=page)


def metadaps(page=''):
    '''Returns a dictionary with all metadaps, paginated'''
    return _paginated('metadaps', page=page)


def daps(page=''):
    '''Returns a dictionary with all daps, paginated'''
    return _paginated('daps', page=page)


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


def search(query, page=''):
    '''Returns a dictionary with the search results, paginated'''
    if page:
        page = '&page={page}'.format(page=page)
    return data(_api_url() + 'search/?q=' + query + page)


def _print_dap_with_description(mdap):
    print(mdap['package_name'], end='')
    latest = mdap['latest_stable'] or mdap['latest']
    if latest:
        latest = data(latest)
        print(' - ', end='')
        print(latest['summary'], end='')
    print('')


def print_users(page=''):
    '''Prints a list of users available on Dapi'''
    u = users(page=page)
    if not u['count']:
        raise Exception('Could not find any users')
    for user in u['results']:
        print(user['username'], end='')
        if user['full_name']:
            print(' (' + user['full_name'] + ')')
        else:
            print('')
    if u['next']:
        print('There are more users available, paginate by --page X')


def print_daps(page=''):
    '''Prints a list of metadaps available on Dapi'''
    m = metadaps(page=page)
    if not m and not page:
        print('Could not find any daps')
        return
    for mdap in m['results']:
        _print_dap_with_description(mdap)
    if m['next']:
        print('There are more daps available, paginate by --page X')


def _get_metadap_dap(name, version=''):
    '''Return data for dap of given or latets version.'''
    m = metadap(name)
    if not m:
        raise Exception('{dap} not found'.format(dap=name))
    if not version:
        d = m['latest_stable'] or m['latest']
        if d:
            d = data(d)
    else:
        d = dap(name, version)
        if not d:
            raise Exception(
                '{dap} doesn\'t have version {version}'.format(dap=name, version=version))
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


def print_search(query, page=''):
    '''Prints the results of a search'''
    m = search(query, page=page)
    if not m['count']:
        raise Exception('Could not find any daps for your query')
        return
    for mdap in m['results']:
        mdap = mdap['content_object']
        _print_dap_with_description(mdap)
    if m['next']:
        print('There are more daps available, paginate by --page X')


def get_installed_daps():
    '''Returns a set of all installed daps'''
    g = []
    for a in 'crt mod prep task'.split():
        g += glob.glob('{d}/assistants/{a}/*.yaml'.format(d=_install_path(), a=a))
    g += glob.glob('{d}/snippets/*.yaml'.format(d=_install_path()))
    s = set()
    for a in g:
        s.add(a.split('/')[-1][:-len('.yaml')])
    return s


def uninstall_dap(name, confirm=False):
    if name not in get_installed_daps():
        raise Exception(
            'Cannot unisnatll {dap}, it is not in {path}'.format(dap=name, path=_install_path()))
    g = []
    for loc in 'assistants files icons'.split():
        g += glob.glob('{d}/{loc}/*/{dap}.*'.format(d=_install_path(), loc=loc, dap=name))
        g += glob.glob('{d}/{loc}/*/{dap}'.format(d=_install_path(), loc=loc, dap=name))
    for loc in 'snippets doc'.split():
        g += glob.glob('{d}/{loc}/{dap}.yaml'.format(d=_install_path(), loc=loc, dap=name))
        g += glob.glob('{d}/{loc}/{dap}'.format(d=_install_path(), loc=loc, dap=name))
    if confirm:
        print('The following files and directories will be removed:')
        for f in g:
            print('    ' + f)
        ok = raw_input('Is that OK? [y/N] ')
        if ok.lower() != 'y':
            print('Aborting')
            return
    for f in g:
        try:
            os.remove(f)
        except OSError:
            shutil.rmtree(f)


def download_dap(name, version='', d='', directory=''):
    '''Download a dap to a given or temporary directory
    Return a path to that file together with information if the directory should be later deleted'''
    if not d:
        m, d = _get_metadap_dap(name, version)
    if directory:
        _dir = directory
    else:
        _dir = tempfile.mkdtemp()
    try:
        url = d['download']
    except TypeError:
        raise Exception('{dap} has no version to download'.format(dap=name))
    filename = url.split('/')[-1]
    path = os.path.join(_dir, filename)
    urllib.urlretrieve(url, path)
    return path, not bool(directory)


def install_dap(name, version='', force=False):
    '''Install a dap from dapi
    If override is True, it will remove previously installed daps of the same name'''
    will_uninstall = False
    if name in get_installed_daps():
        if not force:
            raise Exception('Won\'t override already installed dap')
        else:
            will_uninstall = True
    if os.path.isfile(_install_path()):
        raise Exception(
            '{i} is a file, not a directory'.format(i=_install_path()))
    m, d = _get_metadap_dap(name, version)
    path, remove_dir = download_dap(name, d=d)
    _dir = os.path.dirname(path)
    _extracted_dir = '.'.join(path.split('.')[:-1])
    dap_obj = daploader.Dap(path)
    dap_obj.check()
    dap_obj.extract(_dir)
    try:
        os.remove(os.path.join(_extracted_dir, 'meta.yaml'))
    except:
        pass
    if will_uninstall:
        uninstall_dap(name)
    if not os.path.isdir(_install_path()):
        mkdir(_install_path(), '-p')
    for f in glob.glob(_extracted_dir + '/*'):
        cp('-r', f, _install_path())

    try:
        if remove_dir:
            shutil.rmtree(_dir)
        else:
            os.remove(path)
            shutil.rmtree(_extracted_dir)
    except:
        pass
