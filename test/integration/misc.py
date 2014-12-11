from __future__ import print_function

import atexit
import os
import shutil
import sys
import tempfile

from scripttest import TestFileEnvironment

def run_da(cmd=[], expect_error=False, expect_stderr=False, stdin="", cwd=None, environ=None,
        delete_test_dir=True, top_level_bin='./da.py'):
    # construct command
    if isinstance(cmd, str):
        cmd = cmd.split()
    cmd = [sys.executable, top_level_bin] + cmd

    # create temp dir, register it for removal (or printing that it's a leftover)
    test_dir = tempfile.mkdtemp()
    if delete_test_dir:
        atexit.register(lambda: shutil.rmtree(test_dir))
    else:
        atexit.register(print, 'Leftover test dir: ' + test_dir)

    # make sure we have clean environment
    env = TestFileEnvironment(os.path.join(test_dir, 'test_output'))
    for k in list(env.environ.keys()):
        if k.startswith('DEVASSISTANT'):
            env.environ.pop(k)
    if environ is None:
        env.environ.update({'DEVASSISTANT_NO_DEFAULT_PATH': '1',
            'DEVASSISTANT_HOME': os.path.join(os.path.abspath(env.base_path), '.dahome')})
    else:
        env.environ.update(environ)

    # actually run
    return env.run(*cmd, expect_error=expect_error,
        expect_stderr=expect_stderr, stdin=stdin, cwd=cwd)
