#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import print_function

import os
import subprocess
import sys

import devassistant

try:
    from setuptools import setup, find_packages, Command
except:
    from distutils.core import setup, find_packages, Command

class GeneralTest(Command):
    def finalize_options(self):
        pass

    def runner_exists(self, runner):
        syspaths = os.getenv('PATH').split(os.pathsep)
        for p in syspaths:
            if os.path.exists(os.path.join(p, runner)):
                return True

        return False


class PyTest(GeneralTest):
    user_options = [('test-runner=',
                     't',
                     'test runner to use; by default, multiple py.test runners are tried')]
    command_consumes_arguments = True

    def initialize_options(self):
        self.test_runner = None
        self.args = []

    def run(self):
        # if user provides a runner and it's not found, this fails
        #  otherwise it first tries various versioned runners and if it doesn't
        #  find any, it tries "py.test" - if that's not found either, this fails
        supported = ['2.6', '2.7', '3.3', '3.4']
        potential_runners = ['py.test-' + s for s in supported]
        if self.test_runner:
            potential_runners = [self.test_runner]
        runners = [pr for pr in potential_runners if self.runner_exists(pr)]

        if len(runners) == 0:
            if not self.test_runner and self.runner_exists('py.test'):
                runners = ['py.test']
            else:
                print('No py.test runners found, can\'t run tests.', file=sys.stderr)
                print('Tried: {0}.'.format(', '.join(runners + ['py.test'])), file=sys.stderr)
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


class GUITest(GeneralTest):
    user_options = []
    command_consumes_arguments = True

    def initialize_options(self):
        self.args = []

    def run(self):
        if not self.runner_exists('behave'):
            print('"behave" not found in PATH, can\'t run GUI tests.', file=sys.stderr)
            raise SystemExit(100)

        t = subprocess.Popen(['behave', '-k'] + self.args)
        rc = t.wait()
        raise SystemExit(t.returncode)


def _get_requirements(path):
    with open(path) as f:
        packages = f.read().splitlines()
    packages = (p.strip() for p in packages if not p.startswith('#'))
    packages = list(filter(None, packages))
    return packages

def _install_requirements():
    requirements = _get_requirements('requirements.txt')

    if sys.version_info[0] < 3:
        requirements += _get_requirements('requirements-py2.txt')

    return requirements


description = ''.join(open('README.rst').readlines())

setup(
    name = 'devassistant',
    version = devassistant.__version__,
    description = 'DevAssistant helps you kickstart your projects with ease.',
    long_description = description,
    keywords = 'develop,kickstart,easy,quick',
    author = 'Bohuslav "Slavek" Kabrda',
    author_email = 'bkabrda@redhat.com',
    url = 'https://github.com/bkabrda/devassistant',
    license = 'GPLv2+',
    packages = find_packages(exclude=["test", "*test.*"]),
    include_package_data = True,
    entry_points = {'console_scripts':['da=devassistant.cli.cli_runner:CliRunner.run',
                                       'da-gui=devassistant.gui:run_gui',
                                       'devassistant=devassistant.cli.cli_runner:CliRunner.run',
                                       'devassistant-gui=devassistant.gui:run_gui']},
    install_requires=_install_requirements(),
    setup_requires = [],
    classifiers = ['Development Status :: 4 - Beta',
                   'Environment :: Console',
                   'Intended Audience :: Developers',
                   'License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)',
                   'Operating System :: POSIX :: Linux',
                   'Programming Language :: Python',
                   'Topic :: Software Development',
                  ],
    cmdclass = {'test': PyTest, 'guitest': GUITest}
)
