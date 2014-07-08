# -*- coding: utf-8 -*-
import pytest
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from daploader import dapicli


class TestDapicli(object):
    '''Test if the Dapi CLI works'''

    users_yaml = '''
count: 2
next: null
previous: null
results:
- api_link: http://api/api/users/miro/
  codap_set: []
  fedora_username: churchyard
  full_name: Miro Hroncok
  github_username: hroncok
  human_link: http://api/user/miro/
  id: 1
  metadap_set: ['http://api/api/metadaps/python/', 'http://api/api/metadaps/bar/',
    'http://api/api/metadaps/foo/']
  username: miro
- api_link: http://api/api/users/user/
  codap_set: ['http://api/api/metadaps/python/']
  fedora_username: null
  full_name: ''
  github_username: null
  human_link: http://api/user/user/
  id: 2
  metadap_set: []
  username: user
'''

    search_yaml = '''
count: 1
next: null
previous: null
results:
- content_object:
    active: true
    api_link: http://dapi/api/metadaps/python/
    average_rank: 5.0
    comaintainers: ['http://dapi/api/users/dummy1/']
    dap_set: []
    human_link: http://dapi/dap/python/
    id: 1
    latest: null
    latest_stable: null
    package_name: python
    rank_count: 1
    reports: 0
    similar_daps: ['http://dapi/api/metadaps/bar/']
    tags: [all, python 2, python 3]
    user: http://dapi/api/users/miro/
  content_type: metadap
'''

    def test_print_users(self, capfd):
        '''Test the print of users'''
        desired = 'miro (Miro Hroncok)\nuser\n'
        os.environ['DAPI_FAKE_DATA'] = TestDapicli.users_yaml
        dapicli.print_users()
        out, err = out, err = capfd.readouterr()
        assert out == desired

    def test_search(self, capfd):
        '''Test the print of a search results'''
        desired = 'python\n'
        os.environ['DAPI_FAKE_DATA'] = TestDapicli.search_yaml
        dapicli.print_search('python')
        out, err = out, err = capfd.readouterr()
        assert out == desired
