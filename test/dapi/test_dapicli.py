# -*- coding: utf-8 -*-
import pytest
import os
import six
import sys
import yaml
from flexmock import flexmock

from devassistant import dapi
from devassistant.dapi import dapicli


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
        flexmock(six.moves.builtins).should_receive('open').and_return(flexmock(read=lambda: u'qux'))
        assert dapicli.get_installed_version_of('foo') == version

        # File does not exist
        ioerror = IOError("[Errno 2] No such file or directory: '{0}'".format(yaml_path))
        flexmock(six.moves.builtins).should_receive('open').and_raise(ioerror)

        with pytest.raises(Exception): # TODO maybe change to IOError
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
        fakedap = flexmock(meta={'package_name': 'foo', 'version': '1.0', 'dependencies': ['bar-1.0']}, \
                           check=lambda: True, extract=lambda x: None)
        flexmock(dapi.Dap).new_instances(fakedap)
        flexmock(dapicli).should_receive('get_installed_daps').and_return([])
        flexmock(dapicli).should_receive('_install_path').and_return('.')
        flexmock(dapicli).should_call('install_dap').with_args('bar').never()

        # Filtering off details
        flexmock(os).should_receive('mkdir').and_return()
        flexmock(os).should_receive('rename').and_return()

        dapicli.install_dap_from_path('/foo', nodeps=True)


class TestUninstall(object):

    def setup_class(self):
        self.installed_daps = ['foo', 'bar', 'baz']

    @pytest.mark.parametrize(('confirm', 'result'), [
        ('y', ['foo']),
        ('n', False)
    ])
    def test_uninstall_prompt_works(self, confirm, result, monkeypatch):
        inp = 'input' if six.PY3 else 'raw_input'
        monkeypatch.setattr(six.moves.builtins, inp, lambda x: confirm) # Putting 'y' on fake stdin
        flexmock(dapicli).should_receive('get_installed_daps').and_return(self.installed_daps)
        flexmock(dapicli).should_receive('_get_dependencies_of').and_return([])
        flexmock(dapicli).should_receive('_install_path').and_return('.')
        flexmock(os).should_receive('remove').and_return(None)

        assert dapicli.uninstall_dap('foo', True) == result
