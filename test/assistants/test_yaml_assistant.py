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

    def test_format_command_handles_bool(self):
        # If command is false/true in yaml file, it gets coverted to False/True
        # which is bool object. format_command should handle this.
        assert self.ya.format_command(True) == 'true'
        assert self.ya.format_command(False) == 'false'

    def test_errors(self):
        self.ya._fail_if = [{'cl': 'false'}, {'cl': 'true'}]
        assert self.ya.errors()
