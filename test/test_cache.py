import os
import platform
import shutil
import time

import pytest
import yaml

import devassistant

from devassistant.cache import Cache
from devassistant.exceptions import YamlTypeError
from devassistant import settings
from devassistant.yaml_assistant_loader import YamlAssistantLoader

from test.logger import LoggingHandler

# the paths in this dicts are truncated to make tests pass in any location
# (if not truncated, they contain e.g. home dir on your machine, etc.)
# therefore we need a special comparison method in class below
correct_cache = \
{'crt': {'c': {'attrs': {'args': {'foo': {'flags': ['-f', '--foo'],
                                              'help': 'Help for foo parameter.'}},
                             'description': 'C Language Tool description...',
                             'fullname': 'C Language Tool'},
                   'snippets': {},
                   'ctime': 'dontcheck',
                   'source': 'test/fixtures/assistants/crt/c.yaml',
                   'subhierarchy': {'d': {'attrs': {'args': {'name': {'flags': ['-n',
                                                                                '--name'],
                                                                      'help': 'Name of project to create'},
                                                             'python': {'flags': ['mock'],
                                                                        'help': 'Display python version',
                                                                        'nargs': '?'},
                                                             'some_arg': {'flags': ['-s', '--some-arg'],
                                                                          'gui_hints': {'default': '$(whoami)'}}},
                                                    'fullname': 'D Language Tool'},
                                          'snippets': {'snippet1': 'dontcheck'},
                                          'ctime': 'dontcheck',
                                          'source': 'test/fixtures/assistants/crt/c/d.yaml',
                                          'subhierarchy': {}},
                                    'e': {'attrs': {'args': {'name': {'flags': ['-n',
                                                                                '--name'],
                                                                      'help': 'Name of project to create'}},
                                                    'fullname': 'E Language Tool'},
                                          'snippets': {},
                                          'ctime': 'dontcheck',
                                          'source': 'test/fixtures/assistants/crt/c/e.yaml',
                                          'subhierarchy': {}}}},
             'f': {'attrs': {'args': {'name': {'flags': ['-n', '--name'],
                                               'help': 'Name of project to create'}},
                             'fullname': 'F Language Tool'},
                   'snippets': {},
                   'ctime': 'dontcheck',
                   'source': 'test/fixtures/assistants/crt/f.yaml',
                   'subhierarchy': {'g': {'attrs': {'args': {'name': {'flags': ['-n',
                                                                                '--name'],
                                                                      'help': 'Name of project to create'}},
                                                    'icon_path': '/foo/bar',
                                                    'fullname': 'G Language Tool'},
                                          'snippets': {},
                                          'ctime': 'dontcheck',
                                          'source': 'test/fixtures/assistants/crt/f/g.yaml',
                                          'subhierarchy': {}}}}},
 'twk': {},
 'prep': {},
 'extra': {},
 'version': devassistant.__version__}

class TestCache(object):
    cf = settings.CACHE_FILE
    remove_files = set()
    # Mac tracks ctime in seconds only. See #353 for explanation
    wait = 1 if platform.system() == 'Darwin' else 0.1

    def setup_method(self, method):
        if os.path.exists(self.cf):
            os.unlink(self.cf)
        self.cch = Cache()
        self.tlh = LoggingHandler.create_fresh_handler()

    def teardown_method(self, method):
        while self.remove_files:
            f = self.remove_files.pop()
            if os.path.exists(f):
                os.unlink(f)

    def create_or_refresh_cache(self, roles=settings.ASSISTANT_ROLES, assistants='assistants'):
        for role in roles:
            dirs =[os.path.join(d, assistants, role) for d in settings.DATA_DIRECTORIES]
            fh = YamlAssistantLoader.get_assistants_file_hierarchy(dirs)
            self.cch.refresh_role(role, fh)

    def create_fake_cache(self, struct):
        f = open(self.cch.cache_file, 'w')
        yaml.dump(struct, stream=f)
        f.close()

    def datafile_path(self, path):
        """Assumes that settings.DATA_DIRECTORIES[0] is test/fixtures"""
        return os.path.join(settings.DATA_DIRECTORIES[0], path)

    def addme_copy(self, which, where):
        shutil.copyfile(self.datafile_path(which), self.datafile_path(where))
        self.remove_files.add(self.datafile_path(where))

    def touch_file(self, path):
        os.utime(self.datafile_path(path), None)

    def assert_cache_newer(self, path):
        assert os.path.getctime(self.cch.cache_file) >= os.path.getctime(self.datafile_path(path))

    def assert_cache_content(self, expected, actual):
        assert len(expected) == len(actual)
        for k, v in actual.items():
            assert k in expected
            if k == 'source':
                assert v.endswith(expected[k])
            elif expected[k] == 'dontcheck':
                pass
            else:
                if isinstance(v, dict):
                    self.assert_cache_content(expected[k], v)
                else:
                    assert expected[k] == v

    def test_cache_has_proper_format_on_creation(self):
        self.create_or_refresh_cache()
        self.assert_cache_content(correct_cache, self.cch.cache)

    def test_cache_refreshes_if_assistant_touched(self):
        self.create_or_refresh_cache()
        time.sleep(self.wait)

        p = 'assistants/crt/c.yaml'
        self.touch_file(p)
        self.create_or_refresh_cache()
        self.assert_cache_newer(p)

    def test_cache_refreshes_if_snippet_touched(self):
        self.create_or_refresh_cache()
        time.sleep(self.wait)

        self.cch.snip_ctimes = {}
        p = 'snippets/snippet1.yaml'
        self.touch_file(p)
        self.create_or_refresh_cache()
        self.assert_cache_newer(p)

    def test_cache_doesnt_refresh_if_not_needed(self):
        self.create_or_refresh_cache()
        created = os.path.getctime(self.cch.cache_file)
        time.sleep(self.wait)
        self.create_or_refresh_cache()
        assert created == os.path.getctime(self.cch.cache_file)

    def test_cache_reacts_to_new_changed_removed_assistants(self):
        self.create_or_refresh_cache()

        # add new assistant and test that everything is fine
        self.addme_copy('addme.yaml', 'assistants/crt/addme.yaml')
        self.addme_copy('addme_snippet.yaml', 'snippets/addme_snippet.yaml')
        self.create_or_refresh_cache()
        addme = self.cch.cache['crt']['addme']
        assert 'addme_snippet' in addme['snippets']
        assert len(addme['snippets']) == 1
        assert addme['source'].endswith('assistants/crt/addme.yaml')
        assert addme['attrs']['fullname'] == 'Add me and watch miracles happen'
        assert addme['attrs']['args']['some_arg']['flags'] == ['-x']

        # change assistant fullname
        time.sleep(self.wait)
        self.addme_copy('addme_change_fullname.yaml', 'assistants/crt/addme.yaml')
        self.create_or_refresh_cache()
        assert addme['attrs']['fullname'] == 'Fullname changed!'

        # change current snippet (will change argument flag)
        # snippets are cached during one startup => reset snippet cache manually
        # TODO: fix this ^^
        time.sleep(self.wait)
        self.addme_copy('addme_snippet_changed.yaml', 'snippets/addme_snippet.yaml')
        from devassistant import yaml_snippet_loader; yaml_snippet_loader.YamlSnippetLoader._snippets = {}
        self.cch.snip_ctimes = {}
        self.create_or_refresh_cache()
        addme = self.cch.cache['crt']['addme']
        assert addme['attrs']['args']['some_arg']['flags'] == ['-z']

        # switch assistant to another snippet
        time.sleep(self.wait)
        self.addme_copy('addme_change_snippet.yaml', 'assistants/crt/addme.yaml')
        self.create_or_refresh_cache()
        assert addme['attrs']['args']['some_arg']['flags'] == ['-s', '--some-arg']

        # finally, remove assistant completely
        time.sleep(self.wait)
        os.unlink(self.datafile_path('assistants/crt/addme.yaml'))
        self.create_or_refresh_cache()
        assert 'addme' not in self.cch.cache['crt']

    def test_cache_deletes_if_different_version(self):
        self.create_fake_cache({'version': '0.0.0'})
        prev_time = os.path.getctime(self.cch.cache_file)
        time.sleep(self.wait)
        Cache()
        assert prev_time < os.path.getctime(self.cch.cache_file)

    def test_cache_stays_if_same_version(self):
        self.create_fake_cache({'version': devassistant.__version__})
        prev_time = os.path.getctime(self.cch.cache_file)
        time.sleep(self.wait)
        Cache()
        assert prev_time == os.path.getctime(self.cch.cache_file)

    def test_cache_doesnt_log_higher_than_debug(self):
        # make sure that there's an assistant with an error
        with pytest.raises(YamlTypeError):
            self.create_or_refresh_cache(assistants='assistants_malformed')
        # make sure that there are only DEBUG messages logged
        for msg in self.tlh.msgs:
            assert msg[0] == 'DEBUG'
