#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    from setuptools import setup, find_packages
except:
    from distutils.core import setup, find_packages

setup(
    name='daploader',
    version='0.0.1',
    description='Dap archives loader and checker',
    long_description='Module that loads a dap file, check it for '
                     'sanity/validity and provide access for metadata via'
                     'a class.',
    keywords='devassiatnt, lint, dap',
    author='Miro Hrončok',
    author_email='miro@hroncok.cz',
    license='GPLv2+',
    packages=find_packages(),
    install_requires=['PyYAML'],
    classifiers=['Development Status :: 3 - Alpha',
                 'Intended Audience :: Developers',
                 'License :: OSI Approved :: '
                 'GNU General Public License v2 or later (GPLv2+)',
                 'Operating System :: POSIX :: Linux',
                 'Programming Language :: Python',
                 'Programming Language :: Python :: 2',
                 'Programming Language :: Python :: 2.6',
                 'Programming Language :: Python :: 2.7',
                 'Programming Language :: Python :: 3',
                 'Programming Language :: Python :: 3.3',
                 ]
)
