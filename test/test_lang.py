import os
import re

from devassistant.lang import evaluate_expression, run_section

class TestEvaluate(object):
    def setup_class(self):
        self.names = {"true": True,
                      "false": False,
                      "nonempty": "foo",
                      "nonempty2": "bar",
                      "empty": ""}

        # create directories for test_shell
        os.mkdir(os.path.join(os.path.dirname(__file__), "foo"))
        os.mkdir(os.path.join(os.path.dirname(__file__), "foo", "bar"))
        os.chdir(os.path.dirname(__file__))

    def teardown_class(self):
        os.rmdir(os.path.join(os.path.dirname(__file__), "foo", "bar"))
        os.rmdir(os.path.join(os.path.dirname(__file__), "foo"))

    def test_and(self):
        assert evaluate_expression("$true and $true", self.names) == (True, "")
        assert evaluate_expression("$true and $false", self.names) == (False, "")
        assert evaluate_expression("$false and $true", self.names) == (False, "")
        assert evaluate_expression("$false and $false", self.names) == (False, "")

        assert evaluate_expression("$nonempty and $nonempty2", self.names) == (True, "bar")
        assert evaluate_expression("$nonempty2 and $nonempty", self.names) == (True, "foo")

        assert evaluate_expression("$nonempty and $empty", self.names) == (False, "")
        assert evaluate_expression("$empty and $nonempty", self.names) == (False, "")

        assert evaluate_expression("$nonempty and $true", self.names) == (True, "")
        assert evaluate_expression("$true and $nonempty", self.names) == (True, "")

        assert evaluate_expression("$empty and $true", self.names) == (False, "")
        assert evaluate_expression("$true and $empty", self.names) == (False, "")

        assert evaluate_expression("$empty and $empty", self.names) == (False, "")

        assert evaluate_expression("$true and $nonempty and $nonempty2", self.names) == (True, "")
        assert evaluate_expression("$true and $nonempty and $empty", self.names) == (False, "")

    def test_or(self):
        assert evaluate_expression("$true or $true", self.names) == (True, "")
        assert evaluate_expression("$true or $false", self.names) == (True, "")
        assert evaluate_expression("$false or $true", self.names) == (True, "")
        assert evaluate_expression("$false or $false", self.names) == (False, "")

        assert evaluate_expression("$nonempty or $nonempty2", self.names) == (True, "foo")
        assert evaluate_expression("$nonempty2 or $nonempty", self.names) == (True, "bar")

        assert evaluate_expression("$nonempty or $empty", self.names) == (True, "foo")
        assert evaluate_expression("$empty or $nonempty", self.names) == (True, "foo")

        assert evaluate_expression("$nonempty or $true", self.names) == (True, "foo")
        assert evaluate_expression("$true or $nonempty", self.names) == (True, "foo")

        assert evaluate_expression("$empty or $true", self.names) == (True, "")
        assert evaluate_expression("$true or $empty", self.names) == (True, "")

        assert evaluate_expression("$empty or $empty", self.names) == (False, "")

        assert evaluate_expression("$true or $nonempty or $nonempty2", self.names) == (True, "foo")
        assert evaluate_expression("$false or $nonempty or $empty", self.names) == (True, "foo")

    def test_not(self):
        assert evaluate_expression("not $true", self.names) == (False, "")
        assert evaluate_expression("not $false", self.names) == (True, "")
        assert evaluate_expression("not $nonempty", self.names) == (False, "foo")
        assert evaluate_expression("not $empty", self.names) == (True, "")

    def test_in(self):
        assert evaluate_expression('$nonempty in "foobar"', self.names) == (True, "foo")
        assert evaluate_expression('$nonempty2 in "foobar"', self.names) == (True, "bar")
        assert evaluate_expression('$empty in "foobar"', self.names) == (True, "")
        assert evaluate_expression('$nonempty in "FOOBAR"', self.names) == (False, "foo")

    def test_defined(self):
        assert evaluate_expression("defined $nonempty", self.names) == (True, "foo")
        assert evaluate_expression("defined $empty", self.names) == (True, "")
        assert evaluate_expression("defined $notdefined", self.names) == (False, "")

    def test_variable(self):
        assert evaluate_expression("$true", self.names) == (True, "")
        assert evaluate_expression("$false", self.names) == (False, "")
        assert evaluate_expression("$nonempty", self.names) == (True, "foo")
        assert evaluate_expression("$empty", self.names) == (False, "")

    def test_shell(self):
        assert evaluate_expression("$(echo foobar)", self.names) == (True, "foobar")
        assert evaluate_expression("$(test -d /thoushaltnotexist)", self.names) == (False, '')
        assert evaluate_expression("$(false)", self.names) == (False, '')
        assert evaluate_expression("$(true)", self.names) == (True, '')
        # temporarily disabled
        #assert re.match(".*/foo/bar$",
        #               evaluate_expression("$(cd foo; cd bar; pwd; cd ../..)",
        #                                   self.names)[1])
        assert evaluate_expression('$(echo -e "foo\\nbar" | grep "bar")', self.names) == (True, "bar")

    def test_literal(self):
        assert evaluate_expression('"foobar"', self.names) == (True, "foobar")
        assert evaluate_expression("'foobar'", self.names) == (True, "foobar")
        assert evaluate_expression('""', self.names) == (False, "")

    def test_variable_substitution(self):
        assert evaluate_expression('"$nonempty"', self.names) == (True, "foo")
        assert evaluate_expression('"$empty"', self.names) == (False, "")
        assert evaluate_expression('"$true"', self.names) == (True, "True")

    def test_complex_expression(self):
        assert evaluate_expression('defined $empty or $empty and \
                                    $(echo -e foo bar "and also baz") or "else $nonempty"',
                                    self.names) == (True, 'else foo')

    def test_python_struct(self):
        assert evaluate_expression({'foo': 'bar'}, self.names) == (True, {'foo': 'bar'})
        assert evaluate_expression(['foo', 'bar'], self.names) == (True, ['foo', 'bar'])
        assert evaluate_expression({}, self.names) == (False, {})
        assert evaluate_expression([], self.names) == (False, [])

    def test_special_symbols_in_subshell_invocation(self):
        # before fixing this, special symbols inside shell invocation were
        # surrounded by spaces when parsed reconstructed by evaluate_expression
        # (e.g. backticks, colons, equal signs), e.g. the below command returned
        # (True, '` a : s = d `')
        assert evaluate_expression('$(echo \`a:s=d\`)', {}) == (True, '`a:s=d`')

    def test_variables_in_subshell_invocation(self):
        assert evaluate_expression('$(echo $exists $doesnt)', {'exists': 'X'}) == (True, 'X')

class TestRunSection(object):
    def test_result(self):
        assert run_section([], {}) == [False, '']

        rs = [{'$foo': '$(echo asd)'}]
        assert run_section(rs, {}) == [True, 'asd']

        rs = [{'if $foo': [{'$foo': '"bar"'}, {'$foo': '"baz"'}]}]
        assert run_section(rs, {}) == [False, '']
        assert run_section(rs, {'foo': 'yes'}) == [True, 'baz']
