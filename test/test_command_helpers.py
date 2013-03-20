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

    def test_connect_quoted_both_quote_types_in_first_part(self):
        assert ClHelper._connect_quoted([u'-i',
                                         u'"s|\'NAME\'.',
                                         u"''|'NAME'.",
                                         u'\'asd\'|"',
                                         u'asd/asd/settings.py']) == \
               [u'-i', u"\"s|'NAME'. ''|'NAME'. 'asd'|\"", u'asd/asd/settings.py']
