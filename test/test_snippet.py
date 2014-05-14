import os
import pytest

from devassistant import settings
from devassistant.loaded_yaml import LoadedYaml
from devassistant.snippet import Snippet

class TestSnippet(object):

    @pytest.mark.parametrize(('yaml', 'expected'), [
        ({}, {}),
        ({'args': {}}, {}),
        ({'args': {'foo': 'bar'}}, {'foo': 'bar'})
    ])
    def test_args(self, yaml, expected):
        snip = Snippet('', yaml, '')
        assert snip.args == expected

    @pytest.mark.parametrize(('yaml', 'name', 'expected'), [
        ({}, 'foo', {}),
        ({'args': {'foo': 'bar'}}, 'foo', 'bar')
    ])
    def test_get_arg_by_name(self, yaml, name, expected):
        snip = Snippet('', yaml, '')
        assert snip.get_arg_by_name(name) == expected

    @pytest.mark.parametrize(('yaml', 'section_name', 'expected'), [
        ({}, 'foo', None),
        ({'run': ['foo', 'bar']}, 'run', ['foo', 'bar'])
    ])
    def test_get_run_section(self, yaml, section_name, expected):
        snip = Snippet('', yaml, '')
        assert snip.get_run_section(section_name) == expected

    @pytest.mark.parametrize(('yaml', 'expected'), [
        ({}, os.path.dirname(__file__) + '/fixtures/files/snippets/'),
        ({'files_dir': 'foo'}, 'foo')
    ])
    def test_get_files_dir(self, yaml, expected):
        snip = Snippet('', yaml, '')
        assert snip.get_files_dir() == expected

    @pytest.mark.parametrize(('yaml', 'section_name', 'expected'), [
        ({}, 'dependencies', None),
        ({'dependencies': ['foo']}, 'dependencies', ['foo']),
        ({'dependencies': ['foo'], 'bar': ['baz']}, 'bar', ['foo', 'baz'])
    ])
    def test_get_dependencies_section(self, yaml, section_name, expected):
        snip = Snippet('', yaml, '')
        assert snip.get_dependencies_section(section_name) == expected

    @pytest.mark.parametrize(('yaml', 'expected'), [
        ({}, {}),
        ({'files': 'foo'}, 'foo')
    ])
    def test_get_files_section(self, yaml, expected):
        snip = Snippet('', yaml, '')
        assert snip.get_files_section() == expected


