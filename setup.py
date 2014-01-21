#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    from setuptools import setup, find_packages, Command
except:
    from distutils.core import setup, find_packages, Command

import subprocess
import os

from daploader import __version__


class PyTest(Command):
    user_options = [('test-runner=',
                     't',
                     'test runner to use; by default, multiple py.test runners are tried')]
    command_consumes_arguments = True

    def initialize_options(self):
        self.test_runner = None
        self.args = []

    def finalize_options(self):
        pass

    def runner_exists(self, runner):
        syspaths = os.getenv('PATH').split(os.pathsep)
        for p in syspaths:
            if os.path.exists(os.path.join(p, runner)):
                return True

        return False

    def run(self):
        # only one test runner => just run the tests
        runners = ['py.test-2.7', 'py.test-3.3']
        if self.test_runner:
            runners = [self.test_runner]

        have_runner = False
        for runner in runners:
            if self.runner_exists(runner):
                have_runner = True

        if not have_runner:
            if self.runner_exists('py.test'):
                runners = ['py.test']
            else:
                print('No py.test runners found, can\'t run tests.')
                print('Tried: {0}.'.format(', '.join(runners + ['py.test'])))
                raise SystemExit(100)

        for runner in runners:
            if len(runners) > 1:
                print('\n' * 2)
            print('Running tests using "{0}":'.format(runner))

            retcode = 0
            cmd = [runner]
            for a in self.args:
                cmd.append(a)
            cmd.append('test')
            t = subprocess.Popen(cmd)
            rc = t.wait()
            retcode = t.returncode or retcode

        raise SystemExit(retcode)

setup(
    name='daploader',
    version=__version__,
    description='Dap archives loader and checker',
    long_description='Module that loads a dap file, check it for  sanity/validity and provide access for metadata via a class.',
    keywords='devassiatnt, lint, dap',
    author='Miro Hrončok',
    author_email='miro@hroncok.cz',
    license='GPLv2+',
    packages=find_packages(),
    install_requires=['PyYAML'],
    entry_points={'console_scripts': ['daplint = daploader.daplint:lint']},
    classifiers=['Development Status :: 3 - Alpha',
                 'Intended Audience :: Developers',
                 'License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)',
                 'Operating System :: POSIX :: Linux',
                 'Programming Language :: Python',
                 'Programming Language :: Python :: 2',
                 'Programming Language :: Python :: 2.6',
                 'Programming Language :: Python :: 2.7',
                 'Programming Language :: Python :: 3',
                 'Programming Language :: Python :: 3.3',
                 ],
    cmdclass={'test': PyTest}
)
