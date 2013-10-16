import shlex
import subprocess
import os
from subprocess import Popen
import sys

from devassistant import command
from devassistant import exceptions


class interpreter(object):
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
            raise SyntaxError("Syntax error ({}).".format(self.id))

        def led(self, left):
            raise SyntaxError("Unknown operator ({}).".format(self.id))

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
            raise SyntaxError("Expected {}".format(id))
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
        lexer.wordchars += "$-/\\."

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
            elif tok.startswith('"'):
                # literals
                symbol = self.symbol_table["(literal)"]
                s = symbol()
                s.value = tok.strip('"')
                yield s
            else:
                if not self.in_shell:
                    raise SyntaxError("Unknown token")
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
        self.next = self.tokenize(expression).next
        self.token = self.next()
        return self.expression()


def evaluate_expression(expression, names):
    interpr = interpreter(names)

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

        return bool(self.value), self.value

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
                cmd.append(interpr.token.value)
                interpr.advance()

        cmd = " ".join(cmd)

        # Substitute the variables
        for v in reversed(sorted(interpr.names.keys())):
            cmd = cmd.replace("$" + v, str(interpr.names[v]))

        success = True
        try:
            output = command.Command('cl_n', cmd, interpr.names).run()
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
