import pytest

from devassistant.command_helpers import ClHelper

class TestClHelper(object):
    @pytest.mark.parametrize(('arg_list', 'expected'), [
        (['no', 'change'], ['no', 'change']),
        (['first_with_quote"', 'doesnt break things"'], ['first_with_quote" doesnt break things"']),
        (['"two_quotes_in_one"', 'foo'], ['"two_quotes_in_one"', 'foo']),
        (['"more', 'than', 'one', 'word"'], ['"more than one word"']),
        (['"two_quotes_in_one"', '"foo', 'and_another"'], ['"two_quotes_in_one"', '"foo and_another"']),
    ])
    def test_connect_quoted(self, arg_list, expected):
        assert ClHelper._connect_quoted(arg_list) == expected
