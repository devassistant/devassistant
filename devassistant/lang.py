import re
import sys

from devassistant import command
from devassistant import exceptions
from devassistant.logger import logger
from devassistant import package_managers
from devassistant.yaml_evaluate import evaluate_expression

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
            if dep_type == 'call': # we don't allow general commands, only "call" command here
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
            if comm_type.startswith('$'):
                # intentionally pass kwargs as dict, not as keywords
                assign_variable(comm_type, comm, kwargs)
            elif comm_type.startswith('if'):
                possible_else = None
                if len(section) > i + 1: # do we have "else" clause?
                    possible_else = list(section[i + 1].items())[0]
                _, skip_else, to_run = get_section_from_condition((comm_type, comm), possible_else, kwargs)
                if to_run:
                    # run with original kwargs, so that they might be changed for code after this if
                    run_section(to_run, kwargs, runner=runner)
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
                    run_section(comm, kwargs, runner=runner)
            elif comm_type.startswith('scl'):
                # list of lists of scl names
                kwargs['__scls__'].append(comm_type.split()[1:])
                run_section(comm, kwargs, runner=runner)
                kwargs['__scls__'].pop()
            else:
                command.Command(comm_type,
                                comm,
                                kwargs).run()

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

def get_var_name(dolar_variable):
    name = dolar_variable.strip()
    name = name.strip('"\'')
    if not name.startswith('$'):
        raise exceptions.YamlSyntaxError('Not a proper variable name: ' + dolar_variable)
    name = name[1:] # strip the dollar
    return name.strip('{}')
