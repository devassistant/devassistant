#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
from devassistant.version import VERSION

try:
    from setuptools import setup, Command
except:
    from distutils.core import setup, Command

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

    def run(self):
        import plumbum
        # only one test runner => just run the tests
        runners = ['py.test-2.7', 'py.test-3.3']
        if self.test_runner:
            runners = [self.test_runner]

        for runner in runners:
            if len(runners) > 1:
                print('\n' * 2)
                print('Running tests using "{0}":'.format(runner))

            retcode = 0
            try:
                cmd = plumbum.local[runner]
            except plumbum.commands.CommandNotFound as e:
                print('{0} runner is not present, skipping.'.format(runner))
                continue

            try:
                for a in self.args:
                    cmd = cmd[a]
                (cmd['test']) & plumbum.FG
            except plumbum.ProcessExecutionError as e:
                retcode = 1
                print(e.stdout)

        raise SystemExit(retcode)


description = ''.join(open('README.rst').readlines())

setup(
    name = 'devassistant',
    version = VERSION,
    description = 'Developer assistant helps you kickstart your projects with ease.',
    long_description = description,
    keywords = 'develop,kickstart,easy,quick',
    author = 'Bohuslav "Slavek" Kabrda',
    author_email = 'bkabrda@redhat.com',
    url = 'https://github.com/bkabrda/devassistant',
    license = 'GPLv2+',
    packages = ['devassistant', 'devassistant.assistants', 'devassistant.cli'],
    include_package_data = True,
    entry_points = {'console_scripts':['devassistant=devassistant.bin:CreatorAssistant.main',
                                       'devassistant-modify=devassistant.bin:ModifierAssistant.main']},
    install_requires=['jinja2', 'plumbum', 'PyYaml', 'PyGithub'],
    setup_requires = [],
    classifiers = ['Development Status :: 3 - Alpha',
                   'Environment :: Console',
                   'Intended Audience :: Developers',
                   'License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)',
                   'Operating System :: POSIX :: Linux',
                   'Programming Language :: Python',
                   'Topic :: Software Development',
                  ],
    cmdclass = {'test': PyTest}
)
