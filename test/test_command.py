import pytest

from devassistant.command import Command

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
    def test_format_str(self, comm, arg_dict, result):
        assert Command('cl', comm, self.files_dir, self.files, **arg_dict).format_str() == result

    def test_format_str_handles_bool(self): 
        # If command is false/true in yaml file, it gets coverted to False/True 
        # which is bool object. format should handle this. 
        assert Command('cl', True, self.files_dir, self.files).format_str() == 'true'
        assert Command('cl', False, self.files_dir, self.files).format_str() == 'false'
