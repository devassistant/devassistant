# -*- coding: utf-8 -*-
import pytest
import glob
import os
import six
import sys
import yaml
from flexmock import flexmock

from devassistant import dapi
from devassistant import lang
from devassistant import utils
from devassistant.dapi import dapicli
from devassistant.exceptions import DapiLocalError


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

    def test_format_users(self):
        '''Test the print of users'''
        desired = 'miro (Miro Hroncok)\nuser'
        flexmock(dapicli).should_receive('data').and_return(yaml.load(TestDapicli.users_yaml))
        assert dapicli.format_users() == desired.split('\n')

    def test_search(self, capfd):
        '''Test the print of a search results'''
        desired = utils.bold('python') + '\n'
        flexmock(dapicli).should_receive('data').and_return(yaml.load(TestDapicli.search_yaml))
        for line in dapicli.format_search('python'):
            print(line)
        out, err = capfd.readouterr()
        assert out == desired

    def test_get_installed_version_of_missing_package(self):
        '''Testing updating a DAP'''
        flexmock(dapicli).should_receive('get_installed_daps').and_return(['foo'])
        assert dapicli.get_installed_version_of('bar') is None

    def test_get_installed_version_of(self, capsys):
        install_path = '/foo/bar'
        yaml_path = install_path + 'meta/baz.yaml'
        version = '123'
        flexmock(dapicli).should_receive('get_installed_daps').and_return(['foo'])
        flexmock(dapicli).should_receive('_install_path').and_return(install_path)
        flexmock(yaml).should_receive('load').and_return({'version': version})

        # Everything goes fine
        flexmock(six.moves.builtins).should_receive('open').and_return(
            flexmock(read=lambda: u'qux'))
        assert dapicli.get_installed_version_of('foo') == version

        # File does not exist
        ioerror = IOError("[Errno 2] No such file or directory: '{0}'".format(yaml_path))
        flexmock(six.moves.builtins).should_receive('open').and_raise(ioerror)

        with pytest.raises(Exception):  # TODO maybe change to IOError
            dapicli.get_installed_version_of('foo')

    def test_strip_version_from_dependency(self):
        '''Test a helper funcion _strip_version_from_dependency(dep)'''
        s = dapicli._strip_version_from_dependency
        assert s('foo >= 1') == 'foo'
        assert s('foo>=1') == 'foo'
        assert s('foo == 1') == 'foo'
        assert s('foo==1') == 'foo'
        assert s('foo <=1 ') == 'foo'
        assert s('foo<=1') == 'foo'

    def test_install_from_path_nodeps(self):
        # Functional mocks
        fakedap = flexmock(meta={
            'package_name': 'foo',
            'version': '1.0',
            'dependencies': ['bar-1.0'],
        }, extract=lambda x: None)
        flexmock(dapi.DapChecker).should_receive('check').and_return(True)
        flexmock(dapi.Dap).new_instances(fakedap)
        flexmock(dapicli).should_receive('get_installed_daps').and_return([])
        flexmock(dapicli).should_receive('_install_path').and_return('.')
        flexmock(dapicli).should_call('install_dap').with_args('bar').never()

        # Filtering off details
        flexmock(os).should_receive('mkdir').and_return()
        flexmock(os).should_receive('rename').and_return()

        dapicli.install_dap_from_path('/foo', nodeps=True)

    def test_get_installed_daps_detailed(self):
        '''Test function get_installed_daps_detailed()'''
        flexmock(dapicli).should_receive('_data_dirs').and_return(['/1', '/2', '/3'])

        flexmock(glob).should_receive('glob').with_args('/1/meta/*.yaml').and_return(
            ['/1/meta/a.yaml', '/1/meta/b.yaml', '/1/meta/c.yaml'])
        flexmock(glob).should_receive('glob').with_args('/2/meta/*.yaml').and_return(
            ['/2/meta/a.yaml', '/2/meta/b.yaml'])
        flexmock(glob).should_receive('glob').with_args('/3/meta/*.yaml').and_return(
            ['/3/meta/a.yaml'])

        builtin = 'builtins' if six.PY3 else '__builtin__'
        flexmock(sys.modules[builtin]).should_receive('open').and_return(None)

        flexmock(yaml).should_receive('load').and_return(
            {'version': 1.0})

        expected = {
            'a': [
                {'version': '1.0', 'location': '/1'},
                {'version': '1.0', 'location': '/2'},
                {'version': '1.0', 'location': '/3'},
            ],
            'b': [
                {'version': '1.0', 'location': '/1'},
                {'version': '1.0', 'location': '/2'},
            ],
            'c': [
                {'version': '1.0', 'location': '/1'},
            ],
        }

        details = dapicli.get_installed_daps_detailed()
        assert details == expected



class TestUninstall(object):

    def setup_class(self):
        self.installed_daps = ['foo', 'bar', 'baz']

    def test_uninstall_prompt_works(self):
        flexmock(lang.Command).should_receive('run').and_return((True, True)).once()
        flexmock(dapicli).should_receive('get_installed_daps').and_return(self.installed_daps)
        flexmock(dapicli).should_receive('_get_dependencies_of').and_return([])
        flexmock(dapicli).should_receive('_install_path').and_return('.')
        flexmock(os).should_receive('remove').and_return(None)

        assert dapicli.uninstall_dap('foo', True, __ui__='cli') == ['foo']

        flexmock(lang.Command).should_receive('run').and_return((False, False)).once()
        with pytest.raises(DapiLocalError):
            dapicli.uninstall_dap('foo', True)
