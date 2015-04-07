import pytest
import os

from devassistant import utils

class TestFindFileInLoadDirs(object):
    fixtures = os.path.join(os.path.dirname(__file__), 'fixtures')

    def test_find_ok(self):
        assert utils.find_file_in_load_dirs('files/jinja_template.py') == \
            os.path.join(self.fixtures, 'files', 'jinja_template.py')

    def test_find_not_there(self):
        assert utils.find_file_in_load_dirs('files/does_not_exist') is None


class TestStripPrefix(object):

    @pytest.mark.parametrize(('inp', 'prefix', 'out'), [
        ('foobar', 'foo', 'bar'),
        ('foobar', 'bar', 'foobar'),
        ('foobar', 'foobar', ''),
        ('foo', 'foobar', 'foo'),
        ('foo', str(1), 'foo'),
    ])
    def test_strips(self, inp, prefix, out):
        assert utils.strip_prefix(inp, prefix) == out

    @pytest.mark.parametrize(('inp', 'prefix'), [
        (1, 'foo'),
        (object(), object()),
        ('foo', None)
    ])
    def test_fails(self, inp, prefix):
        with pytest.raises(TypeError) as e:
            utils.strip_prefix(inp, prefix)


class TestStripSuffix(object):

    @pytest.mark.parametrize(('inp', 'suffix', 'out'), [
        ('foobar', 'bar', 'foo'),
        ('foobar', 'r', 'fooba'),
        ('foobar', 'foobar', ''),
        ('foo', 'foobar', 'foo'),
        ('foo', str(1), 'foo'),
    ])
    def test_strips(self, inp, suffix, out):
        assert utils.strip_suffix(inp, suffix) == out

    @pytest.mark.parametrize(('inp', 'suffix'), [
        (1, 'foo'),
        (object(), object()),
        ('foo', None)
    ])
    def test_fails(self, inp, suffix):
        with pytest.raises(TypeError) as e:
            utils.strip_suffix(inp, suffix)
