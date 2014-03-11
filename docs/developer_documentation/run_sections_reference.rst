.. _run_sections_ref:

Run Sections Reference
======================

Run sections are the essence of DevAssistant. They are responsible for
preforming all the tasks and actions to set up the environment and
the project itself. For Creator and Preparer assistants, section named ``run``
is always invoked, :ref:`modifier_assistants_ref` may invoke different sections
based on metadata in ``.devassistant`` file.

Note, that ``pre_run`` and ``post_run`` follow the same rules as ``run`` sections.
See :ref:`assistants_invocation_ref` to find out how and when these sections are invoked.

Every section is a sequence of various **commands**, mostly invocations
of commandline. Each command is a mapping of **command type** to **command input**::

   run:
   - command_runner: command_input
   - command_runner_2: another_command_input

Note, that **section** is a general term used for any sequence of commands. Sections
can have subsections (e.g. in conditions or loops), assuming they follow some rules (see below).

Introduction to Commands and Variables
--------------------------------------

The list of all supported commands can be found at :ref:`command_ref`, we only document
the basic usage of the most important commands here. Note, that when you use variables
(e.g. ``$variable``) in command input, they get substituted for their values
(undefined variables will remain unchanged).

- command line invocation::

     - cl: mkdir -p $spam

  This will invoke a subshell and create a directory named ``$spam``. If the command returns
  non-zero return code, DevAssistant will fail.

- logging::
  
     - log_i: Directory $spam created.

  This command will log the given message at ``INFO`` level - either to terminal or GUI.
  You can use similar commands to log at different log levels: ``log_d`` for ``DEBUG``,
  ``log_w`` for ``WARNING``, ``log_e`` for ``ERROR`` and ``log_c`` for ``CRITICAL``. By default,
  messages of level ``INFO`` and higher are logged. Log messages with levels ``ERROR`` and
  ``CRITICAL`` emit the message and then terminate execution of DevAssistant imediatelly.

- conditions::

    - if not $foo and $(ls /spam/spam/spam):
      - log_i: This gets executed if the condition is satisfied.
    - else:
      - log_i: Else this section gets executed.

  Conditions work as you'd expect in any programming language - ``if`` subsection gets executed if
  the condition evaluates to true, otherwise ``else`` subsection gets executed. The condition
  itself is an **expression**, see :ref:`expressions_ref` for detailed reference of expression.

- loops::

     - for $i in $(ls):
       - log_i: Found file $i.

  Loops probably also work as you'd expect - they've got the control variable and an "iterator".
  Loop iterators are **expressions**, see :ref:`expressions_ref`. The subsection gets executed
  for every word (whitespace-separated substring) of the expression result.

- variable assignment::

     - $foo: "Some literal with value of "foo" variable: $foo"

  This shows how to assign a literal value to a variable. There is also a possibility to assing
  result of another command to variable, see TODO.


Remember to check :ref:`command_ref` for comprehensive description of all commands.

Literal Sections vs. Execution Sections
---------------------------------------

DevAssistant distinguishes two different section types: **input sections** and
**execution sections**. Some sections are inherently execution sections:

- all ``run`` sections of assistants
- ``if``, ``else`` subsections
- ``for`` subsections

Generally, execution sections can be either:

- :ref:`expression <expressions_ref>` (e.g. a Yaml string that gets interpreted as an expression)

or

- section (sequence of **commands**)

Literal section can be any valid Yaml structure - string, list or mapping.

.. _section_results_ref:

Section Results
~~~~~~~~~~~~~~~

Similarly to :ref:`expressions <expressions_ref>`, sections return *logical result* and *result*:

- literal section

  - *result* is a string/list/mapping with variables substituted for their values
  - *logical result* is False if the structure is empty (empty string, list or mapping),
    True otherwise

- execution sections

  - *result* is the result of last command of given section
  - *logical result* is the logical result of last command of given section

Some examples follow::

   run:
   # now we're inherently in execution section
   - if $(ls /foo):
     # now we're also in execution section, e.g. the below sequence is executed
     - foo:
         # the input passed to "foo" command runner is inherently a literal input, e.g. not executed
         # this means foo command runner will get a mapping with two key-value pairs as input, e.g.:
         # {'some': 'string value', 'with': [ ... ]}
         some: string value
         with: [$list, $of, $substituted, $variables]
   - $var: this string gets assigned to "var" with $substituted $variables

If you need to assign result of expression or execution section to a variable or pass it to
a command runner, you need to use the **execution flag**: ``~``::

   run:
   - $foo~: ($this or $gets) and $executed_as_expression
   - foo~:
     # input of "foo" command runner will be result of the below execution section
     - command_runner: literal_section
     - command_runner_2~:
       # similarly, input of command_runner_2 will be result of the below execution section
       - cr: ci
       - cr2: ci2

Each command specifies return value in a different way, see :ref:`command_ref`.

Variables Explained
-------------------

Initially, variables are populated with values of arguments from
commandline/gui and there are no other variables defined for creator
assistants. For modifier assistants global variables are prepopulated
with some values read from ``.devassistant``. You can either define
(and assign to) your own variables or change the values of current ones.

Additionally, after each command, variables ``$LAST_RES`` and ``$LAST_LRES`` are populated
with result of the last command (these are also the return values of the command) -
see :ref:`command_ref`

The variable scope works as follows:

- When invoking a different ``run`` section (from the current assistant or snippet),
  the variables get passed by value (e.g. they don't get modified for the
  remainder of this scope).
- As you would probably expect, variables that get modified in ``if`` and
  ``else`` sections are modified until the end of the current scope.
- Variables defined in subsections (conditions and loops) continue to be available
  even outside of the subsections.

All variables are global in the sense that if you call a snippet or another
section, it can see all the arguments that are defined.

Quoting
~~~~~~~

When using variables that contain user input, they should always be
quoted in the places where they are used for bash execution. That
includes ``cl*`` commands, conditions that use bash return values and
variable assignment that uses bash.

.. _expressions_ref:

Expressions
-----------

Expressions are used in assignments, conditions and as loop "iterables".
Every expression has a *logical result* (meaning success - ``True`` or
failure - ``False``) and *result* (meaning output).  *Logical result*
is used in conditions and variable assignments, *result* is used in
variable assignments and loops.
Note: when assigned to a variable, the *logical result* of an expression can
be used in conditions as expected; the *result* is either ``True`` or ``False``.

Syntax and semantics:

- ``$foo``

  - if ``$foo`` is defined:

    - *logical result*: ``True`` *iff* value is not empty and it is not
      ``False``
    - *result*: value of ``$foo``
  - otherwise:

    - *logical result*: ``False``
    - *result*: empty string

  - *note*: boolean values (e.g. those acquired by argument with ``action: store_true``)
    always have empty string as a *result* and their value as *logical result*

- ``$(commandline command)`` (yes, that is a command invocation that looks like
  running command in a subshell)

  - if ``commandline command`` has return value 0:

    - *logical result*: ``True``

  - otherwise:

    - *logical result*: ``False``

  - regardless of *logical result*, *result* always contains both stdout
    and stderr lines in the order they were printed by ``commandline command``

- ``defined $foo`` - works exactly as ``$foo``, but has *logical result*
  ``True`` even if the value is empty or ``False``

- ``not $foo`` negates the *logical result* of an expression, while leaving
  *result* intact

- ``$foo and $bar``

  - *logical result* is logical conjunction of the two arguments

  - *result* is empty string if at least one of the arguments is empty, or the latter argument

- ``$foo or $bar``

  - *logical result* is logical disjunction of the two arguments

  - *result* is the first non-empty argument or an empty string

- ``literals - "foo", 'foo'``

  - *logical result* ``True`` for non-empty strings, ``False`` otherwise

  - *result* is the string itself, sans quotes

  - *Note: If you use an expression that is formed by just a literal, e.g.* ``"foo"`` *, then
    DevAssistant will fail, since Yaml parser will strip these. Therefore you have to use*
    ``'"foo"'`` *.*

- ``$foo in $bar``

  - *logical result* is ``True`` if the result of the second argument contains the result of the second argument (e.g. "inus" in "Linus Torvalds") and ``False`` otherwise

  - *result* is always the first agument

All these can be chained together, so, for instance, ``"1.8.1.4" in $(git --version)
and defined $git`` is also a valid expression
