from __future__ import print_function

import atexit
import os
import shutil
import sys
import tempfile

import six
from scripttest import TestFileEnvironment


class DATestFileEnvironment(TestFileEnvironment):
    def __init__(self, *args, **kwargs):
        base_path = tempfile.mkdtemp()

        super(DATestFileEnvironment, self).\
            __init__(os.path.join(base_path, 'test_output'), *args, **kwargs)
        # make sure we have clean environment
        for k in list(self.environ.keys()):
            if k.startswith('DEVASSISTANT'):
                self.environ.pop(k)

        env = kwargs.pop('environ', None)
        if env:
            self.environ.update(env)
        else:
            self.environ.update(environ(os.path.join(os.path.abspath(self.base_path), '.dahome')))

        atexit.register(lambda: self.print_leftover(self.base_path))


    def run_da(self, cmd=[], expect_error=False, expect_stderr=False, stdin="", cwd=None,
            environ=None, delete_test_dir=True, top_level_bin='da.py'):
        """Set delete_test_dir to False if you want to inspect it afterwards."""
        # construct command
        if isinstance(cmd, six.string_types):
            cmd = cmd.split()
        if not top_level_bin.startswith(os.path.sep):
            da_topdir = os.path.join(os.path.dirname(__file__), '..', '..')
            top_level_bin = os.path.join(da_topdir, top_level_bin)
        cmd = [sys.executable, top_level_bin] + cmd

        # On 2.6, we got DeprecationWarnings which broke the tests
        # see https://github.com/devassistant/devassistant/issues/381
        if sys.version_info[:2] == (2, 6):
            cmd.insert(1, '-W')
            cmd.insert(2, 'ignore::DeprecationWarning')

        # register base_path for removal (or printing that it's a leftover)
        if delete_test_dir:
            atexit.register(lambda: self.remove_dir_once(self.base_path))

        if environ is not None:
            self.environ = environ

        # Always set the locale to something with UTF-8, otherwise we get ASCII
        self.environ['LC_ALL'] = 'en_US.UTF-8'

        # actually run
        return DAResult(self.run(*cmd, expect_error=expect_error,
            expect_stderr=expect_stderr, stdin=stdin, cwd=cwd))

    def populate_dapath(self, data, path=None):
        """Populates specified entry of DEVASSISTANT_PATH with empty files.
        Populates DEVASSISTANT_HOME if path is None.

        Usage:

        populate_dapath({'assistants': {'crt': ['a.yaml', {'a': ['b.yaml']}]}})
        """
        # here we use the behaviour of os.path.join, which ignores all paths before
        #  last absolute path - if "path" argument is fullpath, it will be used as it is
        dapath = self.environ['DEVASSISTANT_HOME'] if path is None \
            else os.path.join(self.base_path, path)
        if isinstance(data, list):
            for entry in data:
                if isinstance(entry, dict):
                    self.populate_dapath(entry, path=dapath)
                else:
                    open(os.path.join(dapath, entry), 'w').close()
        else:  # dict
            for dir, contents in data.items():
                d = os.path.join(dapath, dir)
                os.makedirs(d)
                self.populate_dapath(contents, path=d)

    def remove_dir_once(self, path):
        if os.path.exists(path):
            shutil.rmtree(path)

    def print_leftover(self, path):
        if os.path.exists(path):
            print('Leftover test dir: ' + path)


class DAResult(object):
    """Wrapper class (not a subclass) for scripttest.ProcResult to be able
    to invoke successive da invocations in the same env.
    """
    def __init__(self, procresult):
        self.__procresult = procresult

    def __getattr__(self, attr):
        return getattr(self.__procresult, attr)

    def run_da(self, *args, **kwargs):
        return self.__procresult.test_env.run_da(*args, **kwargs)

    def populate_dapath(self, data, path=None):
        return self.__procresult.test_env.populate_dapath(data, path=path)


# shortcut for creating DATestFileEnvironment and running run_da
def run_da(*args, **kwargs):
    return DATestFileEnvironment().run_da(*args, **kwargs)

# shortcut for creating DATestFileEnvironment and creating mock DA path inside
def populate_dapath(data, path=None):
    env = DATestFileEnvironment()
    env.populate_dapath(data, path=path)
    return env


def environ(*args, **kwargs):
    '''Return environ dictionary, first dir as home'''
    try:
        home = str(args[0])
    except IndexError:
        return {}
    path = ':'.join([str(x) for x in args[1:]])

    if not kwargs.get('dont_put_home', False):
        path = home + ':' + path

    return {
            'DEVASSISTANT_NO_DEFAULT_PATH': '1',
            'DEVASSISTANT_HOME': home,
            'DEVASSISTANT_PATH': path,
    }
