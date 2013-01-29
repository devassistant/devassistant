#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    from setuptools import setup
except:
    from distutils.core import setup


description = 'Developer assistant'

setup(
    name = 'devassistant',
    version = '0.0.1',
    description = 'Developer assistant',
    long_description = description,
    keywords = 'develop',
    author = 'Bohuslav "Slavek" Kabrda',
    author_email = 'bkabrda@redhat.com',
    url = 'https://github.com/bkabrda/devassistant',
    license = 'GPLv2+',
    packages = ['devassistant', ],
    entry_points = {'console_scripts':['devassistant = devassistant.bin:main']},
    install_requires=[],
    setup_requires = [],
    classifiers = ['Development Status :: 3 - Alpha',
                   'Environment :: Console',
                   'Intended Audience :: Developers',
                   'License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)',
                   'Operating System :: POSIX :: Linux',
                   'Programming Language :: Python',
                   'Topic :: Software Development',
                  ]
)
