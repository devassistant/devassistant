"""This module contains functions that execute assistants' dependencies and run
sections. These functions usually assume that their input has been previously
checked by `devassistant.yaml_checker.check`."""
import os
import re
import shlex
import string
import sys

import six

from devassistant import exceptions
from devassistant.logger import logger
from devassistant import package_managers
from devassistant import settings
from devassistant import utils


class Command(object):
    """A class that represents a Yaml command. It has these members:

    - comm_type: type of command
    - comm: command input as it was specified *literally* (without substitution of vars, etc)
    - input_log_res: logical result of command input
    - input_res: result of command input
    - kwargs: global context taken at point of execution of this command
    """

    command_runners = None

    @classmethod
    def load_command_runners(cls):
        if not cls.command_runners:
            cls.command_runners = utils.import_module('devassistant.command_runners')
        return cls.command_runners

    def __init__(self, comm_type, comm, kwargs={}):
        if '.' in comm_type:
            self.prefix, self.comm_type = comm_type.rsplit('.', 1)
        else:
            self.prefix, self.comm_type = '', comm_type
        self.comm = comm
        self.had_exec_flag = False
        if comm_type.endswith('~'):
            self.comm_type = self.comm_type[:-1]
            self.had_exec_flag = True
        self._input_log_res = None
        self._input_res = None
        self.files_dir = kwargs.get('__files_dir__', [''])[-1]
        self.files = kwargs.get('__files__', [''])[-1]
        self.kwargs = kwargs

    def run(self):
        for crs_prefix, crs in type(self).load_command_runners().command_runners.items():
            if self.prefix == crs_prefix:
                # traverse in reversed order, so that dynamically loaded user command runners
                #  can outrun (=> override) the builtin ones
                for cr in reversed(crs):
                    if cr.matches(self):
                        return cr(self).run()

        prefix_with_colon = self.prefix + '.' if self.prefix else self.prefix
        raise exceptions.CommandException(
            'No runner for command "{p}{ct}: {c}".'.
            format(p=prefix_with_colon, ct=self.comm_type, c=self.input_res))

    @property
    def input_log_res(self):
        return self._eval_input()[0]

    @property
    def input_res(self):
        return self._eval_input()[1]

    def _eval_input(self):
        if self._input_log_res is None:
            runner = self.kwargs.get('__assistant__', None)
            if self.had_exec_flag:
                method = eval_exec_section
            else:
                method = eval_literal_section
            self._input_log_res, self._input_res = method(self.comm, self.kwargs, runner)

        return self._input_log_res, self._input_res


def dependencies_section(section, kwargs, runner=None):
    # "deps" is the same structure as gets returned by "dependencies" method
    skip_else = False
    deps = []

    for i, dep in enumerate(section):
        if getattr(runner, 'stop_flag', False):
            break
        for dep_type, dep_list in dep.items():
            # rpm dependencies (can't handle anything else yet)
            # we don't allow general commands, only "call"/"use" command here
            if dep_type in ['call', 'use']:
                deps.extend(Command(dep_type, dep_list, kwargs).run())
            # handle known types of deps the same, just by appending to "deps" list
            elif dep_type in package_managers.managers.keys():
                fmtd = list(map(lambda dep: format_str(dep, kwargs), dep_list))
                deps.append({dep_type: fmtd})
            elif dep_type.startswith('if'):
                possible_else = None
                if len(section) > i + 1:  # do we have "else" clause?
                    possible_else = list(section[i + 1].items())[0]
                _, skip_else, to_run = get_section_from_condition((dep_type, dep_list),
                                                                  possible_else, kwargs)
                if to_run:
                    deps.extend(dependencies_section(to_run, kwargs, runner=runner))
            elif dep_type == 'else':
                # else on its own means error, otherwise execute it
                if not skip_else:
                    msg = 'Yaml error: encountered "else" with no associated "if", skipping.'
                    logger.error(msg)
                    raise exceptions.YamlSyntaxError(msg)
                skip_else = False
            else:
                logger.warning('Unknown dependency type {0}, skipping.'.format(dep_type))

    return deps


def expand_dependencies_section(section, kwargs):
    """Expands dependency section, e.g. substitues "use: foo" for its contents, but
    doesn't evaluate conditions nor substitue variables."""
    deps = []

    for dep in section:
        for dep_type, dep_list in dep.items():
            if dep_type in ['call', 'use']:
                deps.extend(Command(dep_type, dep_list, kwargs).run())
            elif dep_type.startswith('if ') or dep_type == 'else':
                deps.append({dep_type: expand_dependencies_section(dep_list, kwargs)})
            else:
                deps.append({dep_type: dep_list})

    return deps


def run_section(section, kwargs=None, runner=None):
    if kwargs is None:
        kwargs = {}
    return eval_exec_section(section, kwargs, runner)


def eval_exec_section(section, kwargs, runner=None):
    skip_else = False
    retval = (False, '')

    if isinstance(section, six.string_types):
        return evaluate_expression(section, kwargs)

    for i, command_dict in enumerate(section):
        if getattr(runner, 'stop_flag', False):
            break
        for comm_type, comm in command_dict.items():
            if comm_type.startswith('if'):
                possible_else = None
                if len(section) > i + 1:  # do we have "else" clause?
                    possible_else = list(section[i + 1].items())[0]
                _, skip_else, to_run = get_section_from_condition((comm_type, comm),
                                                                  possible_else, kwargs)
                # run with original kwargs, so that they might be changed for code after this
                if to_run:
                    retval = run_section(to_run, kwargs, runner=runner)
            elif comm_type == 'else':
                if not skip_else:
                    msg = 'Yaml error: encountered "else" with no associated "if", skipping.'
                    raise exceptions.YamlSyntaxError(msg)
                skip_else = False
            elif comm_type.startswith('for '):
                # syntax: "for $i in $x: <section> or "for $i in cl_command: <section>"
                control_vars, eval_expression = get_for_control_var_and_eval_expr(comm_type,
                                                                                  kwargs)
                for i in eval_expression:
                    if len(control_vars) == 2:
                        kwargs[control_vars[0]] = i[0]
                        kwargs[control_vars[1]] = i[1]
                    else:
                        kwargs[control_vars[0]] = i
                    retval = run_section(comm, kwargs, runner=runner)
            elif comm_type.startswith('$'):
                # commands that can have exec flag appended follow
                if comm_type.endswith('~'):  # on exec flag, eval comm as exec section
                    comm_ret = eval_exec_section(comm, kwargs, runner)
                else:  # with no exec flag, eval comm as input section
                    comm_ret = eval_literal_section(comm, kwargs, runner)
                retval = assign_variable(comm_type, *comm_ret, kwargs=kwargs)
            elif comm_type.startswith('catch '):
                was_exc_var, exc_var = get_catch_vars(comm_type)
                try:
                    run_section(comm, kwargs, runner=runner)
                    kwargs[was_exc_var] = False
                    kwargs[exc_var] = ''
                except exceptions.ExecutionException as ex:
                    kwargs[was_exc_var] = True
                    kwargs[exc_var] = utils.exc_as_decoded_string(ex)
                retval = kwargs[was_exc_var], kwargs[exc_var]
            else:
                retval = Command(comm_type, comm, kwargs=kwargs).run()

            if not isinstance(retval, (list, tuple)) or len(retval) != 2:
                raise exceptions.RunException('Bad return value of last command ({ct}: {c}): {r}'.
                                              format(ct=comm_type, c=comm, r=retval))
            assign_last_result(kwargs, *retval)

    return retval


def eval_literal_section(section, kwargs, runner=None):
    retval = (False, '')

    if isinstance(section, six.string_types):
        # two ~~ are an escape sequence (we want to start the string by "~", not
        #  eval it exec section
        eval_exec = False
        if section.startswith('~~'):
            section = section[1:]
        elif section.startswith('~'):
            eval_exec = True

        if eval_exec:
            retval = eval_exec_section(section[1:], kwargs, runner)
        elif is_var(section):
            # if it is a defined variable, return it as it is, not necessarily as string
            # if it is a variable, but not defined, return it's name
            varname = get_var_name(section)
            res = kwargs.get(varname, section)
            retval = (bool(res), res)
        else:
            res = format_str(section, kwargs)
            retval = (bool(res), res)
    elif isinstance(section, list):
        retlist = []
        for item in section:
            retlist.append(eval_literal_section(item, kwargs)[1])
        retval = (bool(retlist), retlist)
    elif isinstance(section, dict):
        retdict = {}
        for k, v in section.items():
            k = format_str(k, kwargs)
            if k.endswith('~'):
                retdict[k[:-1]] = eval_exec_section(v, kwargs, runner)[1]
            else:
                retdict[k] = eval_literal_section(v, kwargs, runner)[1]
        retval = (bool(retdict), retdict)
    else:  # bool, int, float
        retval = (bool(section), section)

    return retval


def assign_last_result(kwargs, log_res, res):
    kwargs[settings.LAST_LR_VAR] = log_res
    kwargs[settings.LAST_R_VAR] = res


def parse_for(control_line):
    """Returns name of loop control variable(s), iteration type (in/word_in) and
    expression to iterate on.

    For example:
    - given "for $i in $foo", returns (['i'], '$foo')
    - given "for ${i} in $(ls $foo)", returns (['i'], '$(ls $foo)')
    - given "for $k, $v in $foo", returns (['k', 'v'], '$foo')
    """
    error = 'For loop call must be in form \'for $var in expression\', got: ' + control_line
    regex = re.compile(r'for\s+(\${?\S+}?)(?:\s*,\s+(\${?\S+}?))?\s+(in|word_in)\s+(\S.+)')
    res = regex.match(control_line)
    if not res:
        raise exceptions.YamlSyntaxError(error)

    groups = res.groups()
    control_vars = []
    control_vars.append(get_var_name(groups[0]))
    if groups[1]:
        control_vars.append(get_var_name(groups[1]))
    iter_type = groups[2]
    expr = groups[3]

    return (control_vars, iter_type, expr)


def get_for_control_var_and_eval_expr(comm_type, kwargs):
    """Returns tuple that consists of control variable name and iterable that is result
    of evaluated expression of given for loop.

    For example:
    - given 'for $i in $(echo "foo bar")' it returns (['i'], ['foo', 'bar'])
    - given 'for $i, $j in $foo' it returns (['i', 'j'], [('foo', 'bar')])
    """
    # let possible exceptions bubble up
    control_vars, iter_type, expression = parse_for(comm_type)
    eval_expression = evaluate_expression(expression, kwargs)[1]

    iterval = []
    if len(control_vars) == 2:
        if not isinstance(eval_expression, dict):
            raise exceptions.YamlSyntaxError('Can\'t expand {t} to two control variables.'.
                                             format(t=type(eval_expression)))
        else:
            iterval = list(eval_expression.items())
    elif isinstance(eval_expression, six.string_types):
        if iter_type == 'word_in':
            iterval = eval_expression.split()
        else:
            iterval = eval_expression
    else:
        iterval = eval_expression

    return control_vars, iterval


def get_section_from_condition(if_section, else_section, kwargs):
    """Returns section that should be used from given if/else sections by evaluating given
    condition.

    Args:
        if_section - section with if clause
        else_section - section that *may* be else clause (just next section after if_section,
                       this method will check if it really is else); possibly None if not present

    Returns:
        tuple (<0 or 1>, <True or False>, section), where
        - the first member says whether we're going to "if" section (0) or else section (1)
        - the second member says whether we should skip next section during further evaluation
          (True or False - either we have else to skip, or we don't)
        - the third member is the appropriate section to run or None if there is only "if"
          clause and condition evaluates to False
    """
    # check if else section is really else
    skip = True if else_section is not None and else_section[0] == 'else' else False
    if evaluate_expression(if_section[0][2:].strip(), kwargs)[0]:
        return (0, skip, if_section[1])
    else:
        return (1, skip, else_section[1]) if skip else (1, skip, None)


def get_catch_vars(catch):
    """Returns 2-tuple with names of catch control vars, e.g. for "catch $was_exc, $exc"
    it returns ('was_exc', 'err').

    Args:
        catch: the whole catch line

    Returns:
        2-tuple with names of catch control variables

    Raises:
        exceptions.YamlSyntaxError if the catch line is malformed
    """
    catch_re = re.compile(r'catch\s+(\${?\S+}?),\s*(\${?\S+}?)')
    res = catch_re.match(catch)
    if res is None:
        err = 'Catch must have format "catch $x, $y", got "{0}"'.format(catch)
        raise exceptions.YamlSyntaxError(err)
    return get_var_name(res.group(1)), get_var_name(res.group(2))


def assign_variable(variable, log_res, res, kwargs):
    """Assigns given result (resp. logical result and result) to a variable
    (resp. to two variables). log_res and res are already computed result
    of an exec/input section. For example:

    $foo~: $spam and $eggs
    $log_res, $foo~: $spam and $eggs

    $foo:
      some: struct
    $log_res, $foo:
      some:
        other:
          struct

    Args:
        variable: variable (or two variables separated by ",") to assign to
        log_res: logical result of evaluated section
        res: result of evaluated section

    Raises:
        YamlSyntaxError: if there are more than two variables
    """
    if variable.endswith('~'):
        variable = variable[:-1]
    comma_count = variable.count(',')
    if comma_count > 1:
        raise exceptions.YamlSyntaxError('Max two variables allowed on left side.')

    if comma_count == 1:
        var1, var2 = map(lambda v: get_var_name(v), variable.split(','))
        kwargs[var1] = log_res
    else:
        var2 = get_var_name(variable)
    kwargs[var2] = res
    return log_res, res


_var_matcher = re.compile(r'^\s*\$\{?([\w]+)\}?\s*$')


def is_var(string):
    return bool(_var_matcher.match(string))


def get_var_name(dollar_variable):
    name = dollar_variable.strip('"\'')
    matched = _var_matcher.match(name)
    if not matched:
        raise exceptions.YamlSyntaxError('Not a proper variable name: ' + dollar_variable)
    return matched.group(1)


# Expression evaluation
class Interpreter(object):
    """
    Interpreter for DevAssistants DSL implemented using Pratt's parser.
    For more info, see:
    * mauke.hopto.org/stuff/papers/p41-pratt.pdf
    * http://javascript.crockford.com/tdop/tdop.html
    * http://effbot.org/zone/simple-top-down-parsing.htm
    """

    def __init__(self, names):
        # A dictionary of variables in the form of {name: value, ...}
        self.names = names

        # A dictionary of symbols in the form of
        # {name of the symbol: its class}
        self.symbol_table = {}

        # Holds the current token
        self.token = None

        # The tokenizer considers all tokens in "$()" to be literals
        self.in_shell = False
        self.as_root = False

    class symbol_base(object):
        id = None
        value = None
        first = second = None

        def nud(self):
            raise SyntaxError("Syntax error ({0}).".format(self.id))

        def led(self, left):
            raise SyntaxError("Unknown operator ({0}).".format(self.id))

    def symbol(self, id, bp=0):
        """
        Adds symbol 'id' to symbol_table if it does not exist already,
        if it does it merely updates its binding power and returns it's
        symbol class
        """

        try:
            s = self.symbol_table[id]
        except KeyError:
            class s(self.symbol_base):
                pass
            s.id = id
            s.lbp = bp
            self.symbol_table[id] = s
        else:
            s.lbp = max(bp, s.lbp)
        return s

    def advance(self, id=None):
        """
        Advance to next token, optionally check that current token is 'id'
        """

        if id and self.token.id != id:
            raise SyntaxError("Expected {0}".format(id))
        self.token = self.next()

    def method(self, symbol_name):
        """
        A decorator - adds the decorated method to symbol 'symbol_name'
        """

        s = self.symbol(symbol_name)

        def bind(fn):
            setattr(s, fn.__name__, fn)
        return bind

    def tokenize(self, program):
        self.in_shell = False
        lexer = shlex.shlex(program)
        lexer.wordchars += "$-/\\.:`!={}~&|"

        for tok in lexer:
            if tok in ["and", "or", "not", "defined", "(", ")", "in", "$", "as_root"]:
                # operators
                symbol = self.symbol_table.get(tok)
                yield symbol()
            elif tok.startswith("$"):
                # names
                symbol = self.symbol_table["(name)"]
                s = symbol()
                s.value = tok[1:]
                yield s
            elif tok.startswith('"') or tok.startswith("'"):
                # literals
                symbol = self.symbol_table["(literal)"]
                s = symbol()
                s.value = tok
                yield s
            else:
                if not self.in_shell:
                    raise SyntaxError("Unknown token: {tok}".format(tok=tok))
                else:
                    # inside shell, everything is a literal
                    symbol = self.symbol_table["(literal)"]
                    s = symbol()
                    s.value = tok
                    yield s
        symbol = self.symbol_table["(end)"]
        yield symbol()

    def expression(self, rbp=0):
        t = self.token
        self.token = self.next()
        left = t.nud()
        while rbp < self.token.lbp:
            t = self.token
            self.token = self.next()
            left = t.led(left)
        return left

    def parse(self, expression):
        """
        Evaluates 'expression' and returns it's value(s)
        """
        if isinstance(expression, (list, dict)):
            return (True if expression else False, expression)
        if sys.version_info[0] > 2:
            self.next = self.tokenize(expression).__next__
        else:
            self.next = self.tokenize(expression).next
        self.token = self.next()
        return self.expression()


def evaluate_expression(expression, names):
    interpr = Interpreter(names)

    # Language definition
    # First, add all the symbols, along with their binding power
    interpr.symbol("and", 10)
    interpr.symbol("or", 10)
    interpr.symbol("not", 10)
    interpr.symbol("in", 10)
    interpr.symbol("defined", 10)
    interpr.symbol("$", 10)
    interpr.symbol("as_root", 10)
    interpr.symbol("(name)")
    interpr.symbol("(literal)")
    interpr.symbol("(end)")
    interpr.symbol("(")
    interpr.symbol(")")

    # Specify the behaviour of each symbol
    # * nud stands for "null denotation" and is used when a token appears
    # at the beginning of a language construct (prefix)
    # * led stand for "left denotation" and is used when it appears inside
    # the construct (infix)
    @interpr.method("(name)")
    def nud(self):
        if self.value in interpr.names:
            value = interpr.names[self.value]
            return bool(value), "" if isinstance(value, bool) else value
        else:
            return False, ""

    @interpr.method("(literal)")
    def nud(self):
        # If there is a known variable in the literal, substitute it for its
        # value
        for v in reversed(sorted(interpr.names.keys())):
            val = interpr.names[v]
            if not six.PY3 and isinstance(val, str):
                val = val.decode(utils.defenc)
            self.value = self.value.replace("$" + v, six.text_type(val))
        # if self.value is in double/single quotes, strip them (but only the outer quotes)
        ret = self.value
        if ret.startswith('"'):
            ret = ret.strip('"')
        elif ret.startswith("'"):
            ret = ret.strip("'")

        return bool(ret), ret

    @interpr.method("and")
    def led(self, left):
        right = interpr.expression(10)

        success = bool(left[0] and right[0])
        output = left[1] and right[1]

        return success, output

    @interpr.method("or")
    def led(self, left):
        right = interpr.expression(10)

        success = bool(left[0] or right[0])
        output = left[1] or right[1]

        return success, output

    @interpr.method("not")
    def nud(self):
        right = interpr.expression(10)

        success = bool(not right[0])
        output = right[1]

        return success, output

    @interpr.method("in")
    def led(self, left):
        success = left[1] in interpr.expression(10)[1]
        output = left[1]

        return success, output

    @interpr.method("defined")
    def nud(self):
        if interpr.token.id != "(name)":
            raise SyntaxError("Expected a name")
        name = interpr.token.value
        interpr.advance()

        success = name in interpr.names
        output = interpr.names[name] if success else ""

        return success, output

    @interpr.method("$")
    def nud(self):
        interpr.in_shell = True
        interpr.advance("(")

        # Gather all the tokens in "$()"
        cmd = []
        if interpr.token.id != ")":
            while 1:
                if interpr.token.id == ")":
                    break
                # if there is (name), tokenizer has already stripped
                # the "$", but we need to keep it for below substitution
                if interpr.token.id == "(name)":
                    interpr.token.value = "$" + interpr.token.value
                cmd.append(interpr.token.value)
                interpr.advance()

        cmd = " ".join(cmd)

        if (cmd.startswith('"') and cmd.endswith('"')) or \
                (cmd.startswith("'") and cmd.endswith("'")):
            cmd = cmd[1:-1]

        success = True
        exec_mode = 'cl_r' if interpr.as_root else 'cl'
        try:
            output = Command(exec_mode, cmd, interpr.names).run()[1]
        except exceptions.RunException as ex:
            success = False
            output = ex.output

        interpr.advance(")")
        interpr.in_shell = False
        interpr.as_root = False

        return success, output

    @interpr.method("as_root")
    def nud(self):
        interpr.as_root = True
        right = interpr.expression(10)
        interpr.as_root = False

        success = bool(right[0])
        output = right[1]

        return success, output

    @interpr.method("(")
    def nud(self):
        self.first = []
        if interpr.token.id != ")":
            while 1:
                if interpr.token.id == ")":
                    break
                self.first.append(interpr.expression())
        interpr.advance(")")

        return bool(self.first[0][0]), self.first[0][1]

    # With the language defined, evaluate the expression
    return interpr.parse(expression)


# spliting strings by _command_splitter.findall(str) preserves whitespace
_command_splitter = re.compile(r'(\s+|\S+)')
# we want to do homedir expansion in quotes (which bash doesn't)
_homedir_matcher = re.compile('\\\\*~')


def _homedir_expand(matchobj):
    # therefore we must hack around this here
    if len(matchobj.group(0)) % 2 == 0:
        # even length => odd number of backslashes => eat one and don't expand
        return matchobj.group(0)[:-2] + '~'
    else:
        # odd length => even number of backslashes => expand an
        return matchobj.group(0)[:-1] + os.path.expanduser('~')


def format_str(s, kwargs):
    files_dir = kwargs.get('__files_dir__', [''])[-1]
    files = kwargs.get('__files__', [{}])[-1]
    # If command is false/true in yaml file, it gets converted to False/True
    # which is bool object => convert
    if isinstance(s, bool):
        comm = str(s).lower()
    else:
        comm = s

    new_comm = []
    parts_list = _command_splitter.findall(comm)

    # replace parts that match something from _files
    for c in parts_list:
        if c.startswith('*'):
            c_file = c[1:].strip('{}')
            if c_file in files:
                new_comm.append(os.path.join(files_dir, files[c_file]['source']))
            else:
                new_comm.append(c)
        else:
            new_comm.append(c)

    new_comm = ''.join(new_comm)

    # substitute cli arguments for their values
    substituted = string.Template(new_comm).safe_substitute(kwargs)

    return _homedir_matcher.sub(_homedir_expand, substituted)
