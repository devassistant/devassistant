import pytest

from devassistant.utils import *

class TestFindFileInLoadDirs(object):
    fixtures = os.path.join(os.path.dirname(__file__), 'fixtures')

    def test_find_ok(self):
        assert find_file_in_load_dirs('files/jinja_template.py') == \
            os.path.join(self.fixtures, 'files', 'jinja_template.py')

    def test_find_not_there(self):
        assert find_file_in_load_dirs('files/does_not_exist') is None
