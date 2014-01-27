import re
import shlex
import sys

from devassistant import command
from devassistant import exceptions
from devassistant.logger import logger
from devassistant import package_managers
from devassistant import settings

if sys.version_info[0] > 2:
    basestring = str

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
                deps.extend(command.Command(dep_type, dep_list, kwargs).run())
            elif dep_type in package_managers.managers.keys(): # handle known types of deps the same, just by appending to "deps" list
                deps.append({dep_type: dep_list})
            elif dep_type.startswith('if'):
                possible_else = None
                if len(section) > i + 1: # do we have "else" clause?
                    possible_else = list(section[i + 1].items())[0]
                _, skip_else, to_run = get_section_from_condition((dep_type, dep_list), possible_else, kwargs)
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

def run_section(section, kwargs, runner=None):
    skip_else = False

    for i, command_dict in enumerate(section):
        if getattr(runner, 'stop_flag', False):
            break
        for comm_type, comm in command_dict.items():
            retval = [False, '']
            if comm_type.startswith('$'):
                # intentionally pass kwargs as dict, not as keywords
                retval = assign_variable(comm_type, comm, kwargs)
            elif comm_type.startswith('if'):
                possible_else = None
                if len(section) > i + 1: # do we have "else" clause?
                    possible_else = list(section[i + 1].items())[0]
                _, skip_else, to_run = get_section_from_condition((comm_type, comm), possible_else, kwargs)
                # run with original kwargs, so that they might be changed for code after this
                if to_run:
                    retval = run_section(to_run, kwargs, runner=runner)
            elif comm_type == 'else':
                if not skip_else:
                    msg = 'Yaml error: encountered "else" with no associated "if", skipping.'
                    raise exceptions.YamlSyntaxError(msg)
                skip_else = False
            elif comm_type.startswith('for'):
                # syntax: "for $i in $x: <section> or "for $i in cl_command: <section>"
                control_vars, eval_expression = get_for_control_var_and_eval_expr(comm_type, kwargs)
                for i in eval_expression:
                    if len(control_vars) == 2:
                        kwargs[control_vars[0]] = i[0]
                        kwargs[control_vars[1]] = i[1]
                    else:
                        kwargs[control_vars[0]] = i
                    retval = run_section(comm, kwargs, runner=runner)
            else:
                retval = command.Command(comm_type,
                                         comm,
                                         kwargs).run()

            if not isinstance(retval, (list, tuple)):
                raise exceptions.RunException('Bad return value of last command ({ct}: {c}): {r}'.\
                        format(ct=comm_type, c=comm, r=retval))
            assign_last_result(kwargs, *retval)

    return [kwargs.get(settings.LAST_LR_VAR, False), kwargs.get(settings.LAST_R_VAR, '')]

def assign_last_result(kwargs, log_res, res):
    kwargs[settings.LAST_LR_VAR] = log_res
    kwargs[settings.LAST_R_VAR] = res

def parse_for(control_line):
    """Returns name of loop control variable(s) and expression to iterate on.

    For example:
    - given "for $i in $foo", returns (['i'], '$foo')
    - given "for ${i} in $(ls $foo)", returns (['i'], 'ls $foo')
    - given "for $k, $v in $foo", returns (['k', 'v'], '$foo')
    """
    error = 'For loop call must be in form \'for $var in expression\', got: ' + control_line
    regex = re.compile(r'for\s+(\${?\S}?)(?:\s*,\s+(\${?\S}?))?\s+in\s+(\S.+)')
    res = regex.match(control_line).groups()
    if not res:
        raise exceptions.YamlSyntaxError(error)

    control_vars = []
    control_vars.append(get_var_name(res[0]))
    if res[1]:
        control_vars.append(get_var_name(res[1]))
    expr = res[2]

    return (control_vars, expr)

def get_for_control_var_and_eval_expr(comm_type, kwargs):
    """Returns tuple that consists of control variable name and iterable that is result
    of evaluated expression of given for loop.

    For example:
    - given 'for $i in $(echo "foo bar")' it returns (['i'], ['foo', 'bar'])
    - given 'for $i, $j in $foo' it returns (['i', 'j'], [('foo', 'bar')])
    """
    # let possible exceptions bubble up
    control_vars, expression = parse_for(comm_type)
    eval_expression = evaluate_expression(expression, kwargs)[1]

    iterval = []
    if len(control_vars) == 2:
        if not isinstance(eval_expression, dict):
            raise exceptions.YamlSyntaxError('Can\'t expand {t} to two control variables.'.\
                    format(t=type(eval_expression)))
        else:
            iterval = list(eval_expression.items())
    elif isinstance(eval_expression, basestring):
        iterval = eval_expression.split()
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

def assign_variable(variable, comm, kwargs):
    """Assigns *result* of expression to variable. If there are two variables separated by
    comma, the first gets assigned *logical result* and the second the *result*.
    The variable is then put into kwargs (overwriting original value, if already there).
    Note, that unlike other methods, this method has to accept kwargs, not **kwargs.

    Even if comm has *logical result* == False, output is still stored and
    this method doesn't fail.

    Args:
        variable: variable (or two variables separated by ",") to assign to
        comm: either another variable or command to run
    """
    comma_count = variable.count(',')
    if comma_count > 1:
        raise exceptions.YamlSyntaxError('Max two variables allowed on left side.')

    res1, res2 = evaluate_expression(comm, kwargs)
    if comma_count == 1:
        var1, var2 = map(lambda v: get_var_name(v), variable.split(','))
        kwargs[var1] = res1
    else:
        var2 = get_var_name(variable)
    kwargs[var2] = res2
    return res1, res2

def is_var(string):
    return string.startswith('$')

def get_var_name(dolar_variable):
    name = dolar_variable.strip()
    name = name.strip('"\'')
    if not name.startswith('$'):
        raise exceptions.YamlSyntaxError('Not a proper variable name: ' + dolar_variable)
    name = name[1:] # strip the dollar
    return name.strip('{}')

### Expression evaluation
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
        lexer.wordchars += "$-/\\.:`={}"

        for tok in lexer:
            if tok in ["and", "or", "not", "defined", "(", ")", "in", "$"]:
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

    ## Language definition
    # First, add all the symbols, along with their binding power
    interpr.symbol("and", 10)
    interpr.symbol("or", 10)
    interpr.symbol("not", 10)
    interpr.symbol("in", 10)
    interpr.symbol("defined", 10)
    interpr.symbol("$", 10)
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
            self.value = self.value.replace("$" + v, str(interpr.names[v]))
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

        # Substitute the variables
        for v in reversed(sorted(interpr.names.keys())):
            cmd = cmd.replace("$" + v, str(interpr.names[v]))

        success = True
        try:
            output = command.Command('cl_n', cmd, interpr.names).run()[1]
        except exceptions.RunException as ex:
            success = False
            output = ex.output

        interpr.advance(")")
        interpr.in_shell = False

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
