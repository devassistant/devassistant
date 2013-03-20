#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    from setuptools import setup, find_packages
except:
    from distutils.core import setup, find_packages

setup(
    name = 'NAME',
    version = '0.0.1',
    description = 'Short description',
    long_description = 'Long description',
    keywords = 'some, keywords',
    author = 'yourname',
    author_email = 'yourmail',
    license = 'GPLv2',
    packages = find_packages(),
    classifiers = ['Development Status :: 3 - Alpha',
                   'Intended Audience :: Developers',
                   'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
                   'Operating System :: POSIX :: Linux',
                   'Programming Language :: Python',
                  ]
)
