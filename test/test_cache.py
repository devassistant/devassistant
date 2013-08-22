import os

from devassistant.cache import Cache
from devassistant import settings
from devassistant.yaml_assistant_loader import YamlAssistantLoader

correct_cache = \
{'creator': {'c': {'attrs': {'args': {'foo': {'flags': ['-f', '--foo'],
                                              'help': 'Help for foo parameter.'}},
                             'description': 'C Language Tool description...',
                             'fullname': 'C Language Tool',
                             'template_dir': '/home/bkabrda/programming/devassistant/test/fixtures/templates'},
                   'snippets': [],
                   'source': '/home/bkabrda/programming/devassistant/test/fixtures/assistants/creator/c.yaml',
                   'subhierarchy': {'d': {'attrs': {'args': {'name': {'flags': ['-n',
                                                                                '--name'],
                                                                      'help': 'Name of project to create'},
                                                             'python': {'flags': ['mock'],
                                                                        'help': 'Display python version',
                                                                        'nargs': '?'},
                                                             'some_arg': {'flags': ['-s',
                                                                                    '--some-arg']}},
                                                    'description': '',
                                                    'fullname': 'D Language Tool',
                                                    'template_dir': '/home/bkabrda/programming/devassistant/test/fixtures/templates'},
                                          'snippets': ['snippet1'],
                                          'source': '/home/bkabrda/programming/devassistant/test/fixtures/assistants/creator/c/d.yaml',
                                          'subhierarchy': {}},
                                    'e': {'attrs': {'args': {'name': {'flags': ['-n',
                                                                                '--name'],
                                                                      'help': 'Name of project to create'}},
                                                    'description': '',
                                                    'fullname': 'E Language Tool',
                                                    'template_dir': '/home/bkabrda/programming/devassistant/test/fixtures/templates'},
                                          'snippets': [],
                                          'source': '/home/bkabrda/programming/devassistant/test/fixtures/assistants/creator/c/e.yaml',
                                          'subhierarchy': {}}}},
             'f': {'attrs': {'args': {'name': {'flags': ['-n', '--name'],
                                               'help': 'Name of project to create'}},
                             'description': '',
                             'fullname': 'F Language Tool',
                             'template_dir': '/home/bkabrda/programming/devassistant/test/fixtures/templates'},
                   'snippets': [],
                   'source': '/home/bkabrda/programming/devassistant/test/fixtures/assistants/creator/f.yaml',
                   'subhierarchy': {'g': {'attrs': {'args': {'name': {'flags': ['-n',
                                                                                '--name'],
                                                                      'help': 'Name of project to create'}},
                                                    'description': '',
                                                    'fullname': 'G Language Tool',
                                                    'template_dir': '/home/bkabrda/programming/devassistant/test/fixtures/templates'},
                                          'snippets': [],
                                          'source': '/home/bkabrda/programming/devassistant/test/fixtures/assistants/creator/f/g.yaml',
                                          'subhierarchy': {}}}}},
 'modifier': {},
 'preparer': {}}

class TestCache(object):
    cf = settings.CACHE_FILE

    def setup_method(self, method):
        if os.path.exists(self.cf):
            os.unlink(self.cf)
        self.cch = Cache()

    def create_cache(self, roles=settings.ASSISTANT_ROLES, assistants='assistants'):
        for role in roles:
            dirs =[os.path.join(d, assistants, role) for d in settings.DATA_DIRECTORIES]
            fh = YamlAssistantLoader.get_assistants_file_hierarchy(dirs)
            self.cch.refresh_role(role, fh)

    def test_foo(self):
        self.create_cache()
        assert self.cch.cache == correct_cache
