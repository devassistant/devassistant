.. _run_sections_ref:

Run Sections Reference
======================

Run sections are the essence of DevAssistant. They are responsible for
performing all the tasks and actions to set up the environment and
the project itself. For Creator and Preparer assistants, the section named ``run``
is always invoked, :ref:`tweak_assistants_ref` may invoke different sections
based on metadata in a ``.devassistant`` file.

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
  ``CRITICAL`` emit the message and then :ref:`raise an exception <run_section_exceptions_ref>`.

- conditions::

    - if not $foo and $(ls /spam/spam/spam):
      - log_i: This gets executed if the condition is satisfied.
    - else:
      - log_i: Else this section gets executed.

  Conditions work as you'd expect in any programming language - ``if`` subsection gets executed if
  the condition evaluates to true, otherwise ``else`` subsection gets executed. The condition
  itself is an **expression**, see :ref:`expressions_ref` for detailed reference of expressions.

- loops::

     - for $i word_in $(ls):
       - log_i: Found file $i.

  Loops probably also work as you'd expect - they've got the control variable and an iterable.
  Loop iterators are **expressions**, see :ref:`expressions_ref`. Note, that you can use two
  forms of for loop. If you use ``word_in``, DevAssistant will split the given expression on
  whitespace and then iterate over that, while if you use ``in``, DevAssistant will iterate
  over single characters of the string.

- variable assignment::

     - $foo: "Some literal with value of "foo" variable: $foo"

  This shows how to assign a literal value to a variable. It is also possible to assign
  the result of another command to a variable, see `Section Results`_ for how to
  use the execution flag.


Remember to check :ref:`command_ref` for a comprehensive description of all commands.

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
   # now we're inherently in an execution section
   - if $(ls /foo):
     # now we're also in an execution section, e.g. the below sequence is executed
     - foo:
         # the input passed to "foo" command runner is inherently a literal input, e.g. not executed
         # this means foo command runner will get a mapping with two key-value pairs as input, e.g.:
         # {'some': 'string value', 'with': [ ... ]}
         some: string value
         with: [$list, $of, $substituted, $variables]
   - $var: this string gets assigned to "var" with $substituted $variables

If you need to assign the result of an expression or execution section to a variable or pass it to
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

Note, that a string starting with the execution flag is also executed as an expression. If you
want to create a literal that starts with ``~``, just use the escape value for it (``~~``)::

   run:
   - $foo: ~$(ls) and $bar
   - $bar: ~~/some_dir_in_users_home
   - log_i: The tilde character (~) only needs to be escaped when starting a string.

Each command specifies its return value in a different way, see :ref:`command_ref`.

.. _run_section_exceptions_ref:

Exceptions
~~~~~~~~~~

If an unexpected error happens in a command runner, then this command runner *raises
exception*. This means that execution of the current section is immediately terminated -
in fact, the whole assistant run is terminated at that moment. In terminology terms, this
is called *raising exception*. Since version 0.11.0, it is possible to
:ref:`catch exceptions <catching_exceptions_ref>`.

For command line execution of DevAssistant, raising exception without catching it means
ending DevAssistant with non-zero return code immediately. In GUI, this means ending the
execution of an assistant, but keeping the GUI running.

.. _variables_ctxt_ref:

Variables and Context
---------------------

The set of all variables existing during an assistant ``run`` section is referred to as
*global context* or just *context* (it is implemented as dictionary, Python's associative
array type). This means, that it is in fact mapping of variable names to their values.

Initially, the context is populated with values of arguments from the
commandline/gui and some other useful values, see :ref:`global_variables_ref` below.
You can of course define (and assign to) your own variables or change the values
of current ones - see :ref:`variable_assignment_ref`. Names of some of the preset
variables start and end with double underscores. You shouldn't modify these, as they
can be used internally by DevAssistant.

Additionally, after each command, variables ``$LAST_RES`` and ``$LAST_LRES`` are populated
with the result of the last command (these are also the return values of the command) -
see :ref:`command_ref`.

The variable scope works as follows:

- When invoking a different ``run`` section (from the current assistant or snippet),
  the variables get passed by value (e.g. they don't get modified for the
  remainder of this scope).
- Variables defined in subsections (``if``, ``else``, ``for``) continue to be available
  until the end of the current ``run`` section.

All variables are global in the sense that if you call a snippet or another
section, it can see all the arguments that are defined.

Quoting
~~~~~~~

When using variables that contain user input, they should always be
quoted in the places where they are used for bash execution. That
includes ``cl*`` commands, conditions that use bash return values and
variable assignment that uses bash.

.. _global_variables_ref:

Global Variables
~~~~~~~~~~~~~~~~

In all assistants, a few useful global variables are available. These include:

- ``$__system_name__`` - name of the system, e.g. "linux"
- ``$__system_version__`` - version of the system, e.g. "3.13.3-201.fc20.x86_64"
- ``$__distro_name__`` - name of Linux distro, e.g. "fedora"
- ``$__distro_version__`` - version of Linux distro, e.g. "20"
- ``$__env__`` - mapping of environment variables that get passed to subprocess shell

Note: if any of this information is not available, the corresponding variable will be empty.
Also note, that you can rely on all the variables having lowercase content.

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
    always have an empty string as a *result* and their value as *logical result*

- ``$(commandline command)`` (yes, that is a command invocation that looks like
  running command in a subshell)

  - if ``commandline command`` has return value 0:

    - *logical result*: ``True``

  - otherwise:

    - *logical result*: ``False``

  - regardless of *logical result*, *result* always contains both stdout
    and stderr lines in the order they were printed by ``commandline command``

  - *note*: Due to the way the expression parser works, DevAssistant may sometimes add spaces
    around special characters between ``$(`` and ``)``. This is a known issue, but we don't have
    any systematic solution right now. The problem can be worked around by putting quotes (single
    or double) around the whole commandline invocation, e.g. you can use ``$("echo +-")``. See
    `issue 271 <https://github.com/devassistant/devassistant/issues/271>`.

- ``as_root $(commandline command)`` runs ``commandline command`` as superuser; DevAssistant
  may achieve this differently on different platforms, so the actual way how this is done
  is considered to be an implementation detail

- ``defined $foo`` - works exactly as ``$foo``, but has *logical result*
  ``True`` even if the value is empty or ``False``

- ``not $foo`` negates the *logical result* of an expression, while leaving
  *result* intact

- ``$foo and $bar``

  - *logical result* is the logical conjunction of the two arguments

  - *result* is an empty string if at least one of the arguments is empty, or the latter argument

- ``$foo or $bar``

  - *logical result* is the logical disjunction of the two arguments

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
