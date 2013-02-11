import pytest

from devassistant.assistants import yaml_assistant

class TestYamlAssistant(object):
    def setup_method(self, method):
        self.ya = yaml_assistant.YamlAssistant()
        self.ya._files = {'first': {'source': 'f/g'}, 'second': {'source': 's/t'}}

    @pytest.mark.parametrize(('comm', 'arg_dict', 'result'), [
        ('ls -la', {}, 'ls -la'),
        ('touch $foo ${bar} $baz', {'foo': 'a', 'bar': 'b'}, 'touch a b $baz'),
        ('cp &first second', {}, 'cp f/g second'),
        ('cp &{first} &{nothing}', {}, 'cp f/g &{nothing}'),
        ('cp &{first} $foo', {'foo': 'a'}, 'cp f/g a'),
    ])
    def test_format_command(self, comm, arg_dict, result):
        assert self.ya.format_command(comm, **arg_dict) == result
