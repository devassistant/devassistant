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
import sys
import logging
from sh import mkdir
from sh import cp

DEFAULT_API_URL = 'http://dapi.devassistant.org/api/'
DEFAULT_USER_INSTALL = '~/.devassistant'
DEFAULT_ROOT_INSTALL = '/usr/local/share/devassistant'


def _api_url():
    return os.environ.get('DAPI_API_URL', DEFAULT_API_URL)


def _install_path():
    path = os.environ.get('DAPI_INSTALL', None)
    if path:
        if path.endswith('/'):
            return os.path.expanduser(path[:-1])
        return os.path.expanduser(path)
    if os.geteuid() == 0:
        return DEFAULT_ROOT_INSTALL
    return os.path.expanduser(DEFAULT_USER_INSTALL)


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
    try:
        count = u['count']
    except KeyError:
        raise Exception('Page over maximum or other 404 error')
    if not count:
        raise Exception('Could not find any users')
    for user in u['results']:
        print(user['username'], end='')
        if user['full_name']:
            print(' (' + user['full_name'] + ')')
        else:
            print('')
    if u['next']:
        print('There are more users available, paginate by adding page number')


def print_daps(page=''):
    '''Prints a list of metadaps available on Dapi'''
    m = metadaps(page=page)
    if not m and not page:
        print('Could not find any daps')
        return
    for mdap in m['results']:
        _print_dap_with_description(mdap)
    if m['next']:
        print('There are more daps available, paginate by adding page number')


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
    try:
        count = m['count']
    except KeyError:
        raise Exception('Page over maximum or other 404 error')
    if not count:
        raise Exception('Could not find any daps for your query')
        return
    for mdap in m['results']:
        mdap = mdap['content_object']
        _print_dap_with_description(mdap)
    if m['next']:
        print('There are more daps available, paginate by adding page number')


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


def install_dap_from_path(path, force=False):
    '''Installs a dap from a given path'''
    will_uninstall = False
    dap_obj = daploader.Dap(path)
    if dap_obj.meta['package_name'] in get_installed_daps():
        if not force:
            raise Exception('Won\'t override already installed dap')
        else:
            will_uninstall = True
    if os.path.isfile(_install_path()):
        raise Exception(
            '{i} is a file, not a directory'.format(i=_install_path()))
    _dir = tempfile.mkdtemp()
    ok = dap_obj.check(level=logging.ERROR)
    if not ok:
        raise Exception('The dap you want to install has errors, won\'t do it')
    dap_obj.extract(_dir)
    if will_uninstall:
        uninstall_dap(dap_obj.meta['package_name'])
    _dapdir = os.path.join(_dir, dap_obj.meta['package_name'] + '-' + dap_obj.meta['version'])
    try:
        os.remove(os.path.join(_dapdir, 'meta.yaml'))
    except:
        pass
    if not os.path.isdir(_install_path()):
        mkdir(_install_path(), '-p')
    for f in glob.glob(_dapdir + '/*'):
        cp('-r', f, _install_path())
    try:
        shutil.rmtree(_dir)
    except:
        pass


def install_dap(name, version='', force=False):
    '''Install a dap from dapi
    If force is True, it will remove previously installed daps of the same name'''
    m, d = _get_metadap_dap(name, version)
    path, remove_dir = download_dap(name, d=d)

    install_dap_from_path(path, force=force)

    try:
        if remove_dir:
            shutil.rmtree(os.dirname(path))
        else:
            os.remove(path)
    except:
        pass


def _eshout(e):
    '''Prints the Exception's message to stderr'''
    sys.stderr.write(str(e))
    sys.stderr.write('\n')


def sync_daps():
    '''For all installed daps, get the latest version from Dapi
    and replace the isntalled dap with it'''
    e = 0
    for name in get_installed_daps():
        print('Updating {dap}'.format(dap=name))
        try:
            install_dap(name, force=True)
        except Exception as e:
            _eshout(e)
            e += 1
    return e


def cli():
    '''Command line client for Dapi'''
    if len(sys.argv) < 2:
        sys.stderr.write('You\'ll need some arguments, try dapi help\n')
        return 1

    if sys.argv[1].endswith('help'):
        print(
            ''.join(open(os.path.join(os.path.dirname(__file__), 'dapi.help')).readlines())
            .format(user=DEFAULT_USER_INSTALL, root=DEFAULT_ROOT_INSTALL),
            end='')
        return

    if (sys.argv[1] == 'install' or sys.argv[1] == 'update'):
        try:
            name = sys.argv[2]
        except:
            sys.stderr.write('You need to say what dap to {what}\n'.format(what=sys.argv[1]))
            return 1
        if os.path.isfile(name):
            try:
                install_dap_from_path(name, sys.argv[1] == 'update')
            except Exception as e:
                _eshout(e)
                return 1
        else:
            try:
                version = sys.argv[3]
            except:
                version = ''
            try:
                install_dap(name, version, sys.argv[1] == 'update')
            except Exception as e:
                _eshout(e)
                return 1
        return

    if (sys.argv[1] == 'search'):
        try:
            query = sys.argv[2]
        except:
            sys.stderr.write('You need to say what to search for\n')
            return 1
        try:
            page = sys.argv[3]
        except:
            page = ''
        try:
            print_search(query, page)
        except Exception as e:
            _eshout(e)
            return 1
        return

    if (sys.argv[1] == 'info'):
        try:
            name = sys.argv[2]
        except:
            sys.stderr.write('You need to say what dap details you want\n')
            return 1
        try:
            version = sys.argv[3]
        except:
            version = ''
        try:
            print_dap(name, version)
        except Exception as e:
            _eshout(e)
            return 1
        return

    if (sys.argv[1] == 'uninstall'):
        try:
            name = sys.argv[2]
        except:
            sys.stderr.write('You need to say what dap to uninstall\n')
            return 1
        try:
            uninstall_dap(name)
        except Exception as e:
            _eshout(e)
            return 1
        return

    if (sys.argv[1] == 'list'):
        for d in get_installed_daps():
            print(d)
        return

    if (sys.argv[1] == 'sync'):
        return sync_daps()

    sys.stderr.write('Unknown command {c}\n'.format(c=sys.argv[1]))
    return 1
