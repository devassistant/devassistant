import pytest
import os
import re

from devassistant.exceptions import YamlSyntaxError
from devassistant.lang import Command, evaluate_expression, exceptions, \
    dependencies_section, format_str, get_var_name,is_var, run_section, parse_for, \
    get_catch_vars

from test.logger import LoggingHandler
# TODO: some of the test methods may need splitting into separate classes according to methods
# that they test; also, the classes should be extended to get better coverage of tested methods


class TestCommand(object):
    def test_command_doesnt_evaluate_if_not_needed(self):
        # will raise exception if it tries to evaluate
        Command('asd', 'sdf')

    def test_command_evaluates_on_input_res_access(self):
        assert Command('log_i', 'foo').input_log_res == True

    def test_command_evaluates_on_input_log_res_access(self):
        assert Command('log_i', 'foo').input_res == 'foo'


class TestDependenciesSection(object):
    @pytest.mark.parametrize('deps, kwargs, result', [
        # simple case
        ([{'rpm': ['foo', '@bar', 'baz']}], {}, None),
        # dependencies in "if" clause apply
        ([{'if $x': [{'rpm': ['foo']}]}, {'else': [{'rpm': ['bar']}]}],
         {'x': 'x'},
         [{'rpm': ['foo']}]),
        # dependencies in "else" clause apply
        ([{'if $x': [{'rpm': ['foo']}]}, {'else': [{'rpm': ['bar']}]}], {}, [{'rpm': ['bar']}])
    ])
    def test_dependencies(self, deps, kwargs, result):
        dependencies_section(deps, kwargs) == deps if result == None else deps


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
        # surrounded by spaces when parsed and reconstructed by evaluate_expression
        # (e.g. backticks, colons, equal signs), e.g. the below command returned
        # (True, '` a : s = d ...)
        assert evaluate_expression('$(echo \`a:s!=d\`\~\&\|)', {}) == (True, '`a:s!=d`~&|')

    def test_workaround_for_more_special_symbols(self):
        # see https://github.com/devassistant/devassistant/issues/271
        assert evaluate_expression('$("echo +-")', {}) == (True, '+-')
        assert evaluate_expression("$('echo +-')", {}) == (True, '+-')

    def test_variables_in_subshell_invocation(self):
        assert evaluate_expression('$(echo $exists $doesnt)', {'exists': 'X'}) == (True, 'X')
        assert evaluate_expression('$(echo ${exists} ${doesnt})', {'exists': 'X'}) == (True, 'X')

    def test_env(self):
        res = evaluate_expression('$(echo $DEVASSISTANTTESTFOO)', {'DEVASSISTANTTESTFOO': 'foo'})
        assert res == (True, 'foo')


class TestRunSection(object):
    def setup_method(self, method):
        self.tlh = LoggingHandler.create_fresh_handler()

    def assert_run_section_result(self, actual, expected):
        # "actual" can possibly be a tuple, not a list, so we need to unify the value
        assert list(actual) == list(expected)

    def test_result(self):
        self.assert_run_section_result(run_section([]), [False, ''])
        self.assert_run_section_result(run_section([{'log_i': 'foo'}]), [True, 'foo'])

    def test_run_unkown_command(self):
        with pytest.raises(exceptions.CommandException):
            run_section([{'foo': 'bar'}])

    def test_shell_command(self):
        rs = [{'$foo~': '$(echo asd)'}]
        self.assert_run_section_result(run_section(rs, {}), [True, 'asd'])

    def test_looks_like_shell_command_but_no_exec_flag(self):
        rs = [{'$foo': '$(echo asd)'}]
        self.assert_run_section_result(run_section(rs, {}), [True, '$(echo asd)'])

    def test_if(self):
        rs = [{'if $foo': [{'$foo': 'bar'}, {'$foo': 'baz'}]}]
        self.assert_run_section_result(run_section(rs, {}), [False, ''])
        self.assert_run_section_result(run_section(rs, {'foo': 'yes'}), [True, 'baz'])

    def test_nested_condition(self):
        rs = [{'if $foo': [{'if $bar': 'bar'}, {'else': [{'log_i': 'baz'}]}]}]
        self.assert_run_section_result(run_section(rs, {'foo': 'yes'}), [True, 'baz'])

    def test_else(self):
        rs = [{'if $foo': [{'$foo': 'bar'}]}, {'else': [{'$foo': 'baz'}]}]
        self.assert_run_section_result(run_section(rs, {'foo': 'yes'}), [True, 'bar'])
        self.assert_run_section_result(run_section(rs, {}), [True, 'baz'])

    def test_for_in_string(self):
        rs = [{'for $i in $list': [{'$foo~': '$(echo $i)'}]}]
        self.assert_run_section_result(run_section(rs, {'list': 'fo'}), [True, 'o'])
        self.assert_run_section_result(run_section(rs, {'list': 'fo ba'}), [True, 'a'])
        self.assert_run_section_result(run_section(rs, {}), [False, ''])

    def test_for_word_in_string(self):
        rs = [{'for $i word_in $list': [{'$foo~': '$(echo $i)'}]}]
        self.assert_run_section_result(run_section(rs, {'list': 'fo'}), [True, 'fo'])
        self.assert_run_section_result(run_section(rs, {'list': 'fo ba'}), [True, 'ba'])
        self.assert_run_section_result(run_section(rs, {}), [False, ''])

    @pytest.mark.parametrize('control_line, output', [
        ('for $i in $j', (['i'], 'in', '$j')),
        ('for $multichar in $secondmultichar', (['multichar'], 'in', '$secondmultichar')),
        ('for $multi1, $multi2 in $multi3', (['multi1', 'multi2'], 'in', '$multi3')),
        ('for  $i  ,     $j in  $k', (['i', 'j'], 'in', '$k')),
        ('for $i in $this and $that', (['i'], 'in', '$this and $that')),
    ])
    def test_for_control_line_parsing(self, control_line, output):
        # there's a pretty complicated regexp for checking the control line, so let's
        #  check some of the correct variants
        assert parse_for(control_line) == output

    def test_for_empty_string(self):
        kwargs = {}
        run_section([{'for $i in $(echo "")': [{'$foo': '$i'}]}], kwargs)
        assert 'foo' not in kwargs

    def test_for_list(self):
        kwargs = {'a': ['asd', 'sdf']}
        run_section([{'for $i in $a': [{'log_i': '$i'}]}], kwargs)
        assert ('INFO', 'asd') in self.tlh.msgs
        assert ('INFO', 'sdf') in self.tlh.msgs

    @pytest.mark.parametrize('iter_type', [
        'in',
        'word_in'
    ])
    def test_loop_two_control_vars(self, iter_type):
        # this should work the same for both iteration types
        tlh = LoggingHandler.create_fresh_handler()
        run_section([{'for $i, $j {0} $foo'.format(iter_type): [{'log_i': '$i, $j'}]}],
                    {'foo': {'bar': 'barval', 'spam': 'spamval'}})
        assert ('INFO', 'bar, barval') in tlh.msgs
        assert ('INFO', 'spam, spamval') in tlh.msgs

    @pytest.mark.parametrize('iter_type', [
        'in',
        'word_in'
    ])
    def test_loop_two_control_vars_fails_on_string(self, iter_type):
        # this should work the same for both iteration types
        with pytest.raises(exceptions.YamlSyntaxError):
            run_section([{'for $i, $j {0} $(echo "foo bar")'.format(iter_type):
                            [{'log_i': '$i'}]}])

    @pytest.mark.parametrize('comm', [
        'for foo',
        'for $a foo'])
        # Not sure if 'for $a in $var something' should raise
    def test_parse_for_malformed(self, comm):
        with pytest.raises(exceptions.YamlSyntaxError):
            parse_for(comm)

    @pytest.mark.parametrize(('comm', 'result'), [
        ('for $a in $foo',          (['a'], 'in', '$foo')),
        ('for $a in $(expr)',       (['a'], 'in', '$(expr)')),
        ('for $a, $b in $foo',      (['a', 'b'], 'in', '$foo')),
        ('for $a, $b in $(expr)',   (['a', 'b'], 'in', '$(expr)')),
        ('for ${a} in $foo',        (['a'], 'in', '$foo')),
        ('for ${a} in $(expr)',     (['a'], 'in', '$(expr)')),
        ('for ${a}, ${b} in $foo',  (['a', 'b'], 'in', '$foo')),
        ('for ${a}, ${b} in $(expr)', (['a', 'b'], 'in', '$(expr)')),
        # also test "word_in for few simple cases"
        ('for $a word_in $foo',     (['a'], 'word_in', '$foo')),
        ('for $a, $b word_in $foo', (['a', 'b'], 'word_in', '$foo')),
        ('for ${a} word_in $foo',   (['a'], 'word_in', '$foo')),
        ('for ${a}, ${b} word_in $foo', (['a', 'b'], 'word_in', '$foo')),

    ])
    def test_parse_for_well_formed(self, comm, result):
        assert(parse_for(comm) == result)

    def test_successful_command_with_no_output_evaluates_to_true(self):
        kwargs = {}
        run_section([{'if $(true)': [{'$success': 'success'}]}], kwargs)
        assert 'success' in kwargs

    def test_assign_in_condition_modifies_outer_scope(self):
        kwargs={'foo': 'foo', 'spam': 'spam'}
        run_section([{'if $foo': [{'$foo': '$spam'}]}], kwargs)
        assert kwargs['foo'] == 'spam'

    def test_assign_existing_nonempty_variable(self):
        kwargs = {'bar': 'bar'}
        run_section([{'$foo': '$bar'}], kwargs)
        assert kwargs['foo'] == 'bar'

        # both logical result and result
        run_section([{'$success, $val': '$bar'}], kwargs)
        assert kwargs['success'] == True
        assert kwargs['val'] == 'bar'

    @pytest.mark.parametrize('exec_flag, lres, res', [
        ('', False, ''), # no exec flag => evals as literal
        ('~', False, '')
    ])
    def test_assign_existing_empty_variable(self, exec_flag, lres, res):
        kwargs = {'bar': ''}
        run_section([{'$foo{0}'.format(exec_flag): '$bar'}], kwargs)
        assert kwargs['foo'] == res

        # both logical result and result
        run_section([{'$success, $val{0}'.format(exec_flag): '$foo'}], kwargs)
        assert kwargs['success'] == lres
        assert kwargs['val'] == res

    @pytest.mark.parametrize('exec_flag, lres, res', [
        ('', True, '$bar'), # no exec flag => evals as literal
        ('~', False, '')
    ])
    def test_assign_nonexisting_variable_depending_on_exec_flag(self, exec_flag, lres, res):
        kwargs = {}
        run_section([{'$foo{0}'.format(exec_flag): '$bar'}], kwargs)
        assert kwargs['foo'] == res

        # both logical result and result
        run_section([{'$success, $val{0}'.format(exec_flag): '$bar'}], kwargs)
        assert kwargs['success'] == lres
        assert kwargs['val'] == res

    def test_assign_defined_empty_variable(self):
        kwargs = {'foo': ''}
        run_section([{'$success, $val~': 'defined $foo'}], kwargs)
        assert kwargs['success'] == True
        assert kwargs['val'] == ''

    def test_assign_defined_variable(self):
        kwargs = {'foo': 'foo'}
        run_section([{'$success, $val~': 'defined $foo'}], kwargs)
        assert kwargs['success'] == True
        assert kwargs['val'] == 'foo'

    def test_assign_defined_nonexistent_variable(self):
        kwargs = {}
        run_section([{'$success, $val~': 'defined $foo'}], kwargs)
        assert kwargs['success'] == False
        assert kwargs['val'] == ''

    def test_assign_successful_command(self):
        kwargs = {}
        run_section([{'$foo~': '$(basename foo/bar)'}, {'log_i': '$foo'}], kwargs)
        assert kwargs['foo'] == u'bar'

        # both logical result and result
        run_section([{'$success, $val~': '$(basename foo/bar)'}], kwargs)
        assert kwargs['success'] == True
        assert kwargs['val'] == 'bar'

    def test_assign_unsuccessful_command(self):
        kwargs = {}
        run_section([{'$foo~': '$(ls spam/spam/spam)'}], kwargs)
        assert re.match(r'ls:.* spam/spam/spam: No such file or directory', kwargs['foo'], re.I|re.M)

        # both logical result and result
        run_section([{'$success, $val~': '$(ls spam/spam/spam)'}], kwargs)
        # assert kwargs['val'] == u'ls: cannot access spam/spam/spam: No such file or directory'
        assert re.match(r'ls:.* spam/spam/spam: No such file or directory', kwargs['val'], re.I|re.M)
        assert kwargs['success'] == False

    def test_assing_string_with_escaped_exec_flag(self):
        kwargs = {}
        run_section([{'$foo': '~~/asd'}], kwargs)
        assert kwargs['foo'] == os.path.expanduser('~/asd')

    def test_bool_literal_section(self):
        kwargs = {}
        run_section([{'$foo': True}], kwargs)
        assert kwargs['foo'] == True

    def test_numeric_literal_section(self):
        kwargs = {}
        run_section([{'$foo': 42}, {'$bar': 4.2}], kwargs)
        assert kwargs['foo'] == 42
        assert kwargs['bar'] == 4.2

    @pytest.mark.parametrize('input, output', [
        ('catch $was_exc, $exc', ('was_exc', 'exc')),
        ('catch $x,$y', ('x', 'y')),
    ])
    def test_get_catch_vars_ok(self, input, output):
        assert get_catch_vars(input) == output

    @pytest.mark.parametrize('input', [
        'catch $was_exc',
        'catch $was_exc, $x, $y',
    ])
    def test_get_catch_vars_malformed(self, input):
        with pytest.raises(YamlSyntaxError):
            get_catch_vars(input)

    def test_catch(self):
        kwargs = {}
        res = run_section(
            [{'catch $x, $y': [{'cl': 'ls this_doesnt_exist_and_thus_will_raise'}]}],
            kwargs)
        assert res[0] == True
        assert res[1] != ''

    def test_catch_no_exception(self):
        kwargs = {}
        res = run_section([{'catch $x, $y': [{'cl': 'true'}]}])
        assert res[0] == False
        assert res[1] == ''


class TestIsVar(object):
    @pytest.mark.parametrize(('tested', 'expected'), [
        ('$normal', True),
        ('${curly}', True),
        ('  $whitespace_around  ', True),
        ('$CAPS', True),
        ('$___', True),
        ('no_dolar', False),
        ('$whitespace in var', False),
    ])
    def test_is_var(self, tested, expected):
        assert is_var(tested) == expected


class TestGetVarName(object):
    @pytest.mark.parametrize(('tested', 'expected'), [
        ('$normal', 'normal'),
        ('${curly}', 'curly'),
        ('  $whitespace_around  ', 'whitespace_around'),
        ('$CAPS', 'CAPS'),
        ('$___', '___'),
        ('no_dolar', None),
        ('$whitespace in var', None),
    ])
    def test_get_var_name(self, tested, expected):
        if expected is None:
            with pytest.raises(YamlSyntaxError):
                get_var_name(tested)
        else:
            assert get_var_name(tested) == expected


class TestFormatStr(object):
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
        arg_dict['__files__'] = [self.files]
        arg_dict['__files_dir__'] = [self.files_dir]
        assert format_str(comm, arg_dict) == result

    def test_format_str_handles_bool(self):
        # If command is false/true in yaml file, it gets coverted to False/True
        # which is bool object. format should handle this.
        assert format_str(True, {}) == 'true'
        assert format_str(False, {}) == 'false'

    def test_format_str_preserves_whitespace(self):
        c = "  eggs   spam    beans  "
        assert format_str(c, {}) == c

    def test_format_str_with_homedir(self):
        c = "~/foo"
        assert format_str(c, {}) == os.path.expanduser('~/foo')
