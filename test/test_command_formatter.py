import pytest

from devassistant.command_formatter import CommandFormatter

class TestCommandFormatter(object):
    files_dir = '/a/b/c'
    files = {'first': {'source': 'f/g'}, 'second': {'source': 's/t'}}

    @pytest.mark.parametrize(('comm', 'arg_dict', 'result'), [
        ('ls -la', {}, 'ls -la'),
        ('touch $foo ${bar} $baz', {'foo': 'a', 'bar': 'b'}, 'touch a b $baz'),
        ('cp *first second', {}, 'cp {0}/f/g second'.format(files_dir)),
        ('cp *{first} *{nothing}', {}, 'cp %s/f/g *{nothing}' % (files_dir)),
        ('cp *{first} $foo', {'foo': 'a'}, 'cp {0}/f/g a'.format(files_dir)),
    ])
    def test_format(self, comm, arg_dict, result):
        assert CommandFormatter.format('cl', comm, self.files_dir, self.files, **arg_dict) == result

    def test_format_handles_bool(self): 
        # If command is false/true in yaml file, it gets coverted to False/True 
        # which is bool object. format should handle this. 
        assert CommandFormatter.format('cl', True, self.files_dir, self.files) == 'true'
        assert CommandFormatter.format('cl', False, self.files_dir, self.files) == 'false'
