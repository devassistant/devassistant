.. _command_ref:

Command Reference
=================

This page serves as a reference commands of DevAssistant Yaml DSL.
Every command consists of **command_type** and **command_input** and sets ``LAST_LRES`` and
``LAST_RES`` variables. These two should represent (similarly to :ref:`expressions_ref` **logical
result** and **result**):

- ``LAST_LRES`` - a logical result of the run - ``True``/``False`` if successful/unsuccessful
- ``LAST_RES`` - a "return value" - e.g. a computed value

*Missing something?* Commands are your entrypoint for extending DevAssistant.
If you're missing some functionality in ``run`` sections, just
:ref:`write a command runner <command_runners>` and send us a pull request.

Assign To Variable
------------------

Assign *result* (and possibly also *logical result*) of :ref:`expressions_ref`
to a variable.

``$<var1>[, $<var2>]`` - if one variable is given, *result* of expression (**command input**)
is assigned. If two variables are given, the first gets assigned *logical result* and the
second *result*.

- Input: an expression
- RES: *result* of the expression
- LRES: *logical result* of the expression
- Example::

    $foo: "bar"
    $spam:
    - spam
    - spam
    - spam
    $bar: $baz
    $success, $list: $(ls "$foo")

Flow Control Commands
---------------------

Conditional execution and loops. The expressions must follow rules in :ref:`expressions_ref`.

``if <expression>``, ``else`` - conditionally execute one or the other section (``if`` can
stand alone, of course)

- Input: a subsection to run
- RES: RES of last command in the subsection, if this clause is invoked. If not invoked,
  there is no RES.
- LRES: LRES of last command in the subsection, if this clause is invoked. If not invoked,
  there is no LRES.
- Example::

    if defined $foo:
    - log_i: Foo is $foo!
    else:
    - log_i: Foo is not defined!

``for <var>[, <var>] in <expression>`` - loop over result of the expression (strings are
split in whitespaces). When iterating over mapping, two control variables may be provided
to get both key and its value.

- Input: a subsection to repeat in loop
- RES: RES of last command of last iteration in the subsection. If there are no interations,
  there is no RES.
- LRES: LRES of last command of last iteration in the subsection. If there are no interations,
  there is no RES.
- Example::

     for $i in $(ls):
     - log_i: $i

     $foo:
       1: one
       2: two
     for $k, $v in $foo:
     - log_i: $k, $v


Ask Commands
------------

User interaction commands, let you ask for password and various other input.

``ask_password``

- Input: list of

  - *variable* that gets assigned the password (empty if user denies)
  - mapping containing ``prompt`` (short prompt for user)

- RES: the password
- LRES: always ``True``
- Example::

     ask_password:
     - $passwd
     - prompt: "Please provide your password"



``ask_confirm``

- Input: list of

  - *variable* that gets assigned the confirmation (``True``/``False``)
  - mapping containing ``prompt`` (short prompt for user) and ``message`` (a longer description
    of what the user should confirm

- RES: the confirmation
- LRES: always ``True``
- Example::

    ask_confirm:
    - $confirmed
    - message: "Do you think DevAssistant is great?"
      prompt: "Please select yes."

Command Line Commands
---------------------

Run commands in subprocesses and receive their output.

``cl``, ``cl_i`` (these do the same, but the second version logs the command output on INFO level,
therefore visible to user by default)

- Input: a string, possibly containing variables and references to files
- RES: stdout + stdin interleaved as they were returned by the executed process
- LRES: always ``True`` (if the command fails, the whole DevAssistant execution fails)
- Example::

    cl: mkdir ${name}
    cl: cp *file ${name}/foo


Dependencies Command
--------------------

Install dependencies from given **command input**.

``dependencies``

- Input: list of mappings, similar to :ref:`Dependencies section <dependencies_ref>`, but without
  conditions and usage of sections from snippets etc.
- RES: always ``True`` (terminates DevAssistant if dependency installation fails)
- LRES: **command input**, but with expanded variables
- Example::

    if $foo:
    - $rpmdeps: [foo, bar]
    else:
    - $rpmdeps: []

    dependencies:
    - rpm: $rpmdeps

.devassistant Commands
----------------------

Commands that operate with ``.devassistant`` file.

``dda_c`` - creates a ``.devassistant`` file, should only be used in creator assistants

- Input: directory where the file is supposed to be created
- RES: always ``True``, terminates DevAssistant if something goes wrong
- LRES: always empty string
- Example::

    dda_c: ${path}/to/project

``dda_r`` - reads an existing ``.devassistant`` file, should be used by modifier and preparer
assistants.Sets some global variables accordingly, most importantly ``original_kwargs`` (arguments
used when the project was created) - these are also made available with ``dda__`` prefix (yes,
that's double underscore).

- Input: directory where the file is supposed to be
- RES: always ``True``, terminates DevAssistant if something goes wrong
- LRES: always empty string
- Example::

    dda_r: ${path}/to/project

``dda_dependencies`` - installs dependencies from ``.devassistant`` file, should be used by
preparer assistants. Utilizes both dependencies of creator assistants that created this project
plus dependencies from ``dependencies`` section, if present (this section is evaluated in the
context of current assistant, not the creator).

- Input: directory where the file is supposed to be
- RES: always ``True``, terminates DevAssistant if something goes wrong
- LRES: always empty string
- Example::

    dda_dependencies: ${path}/to/project

``dda_run`` - run ``run`` section from from ``.devassistant`` file, should be used by
preparer assistants. This section is evaluated in the context of current assistant, not the
creator.

- Input: directory where the file is supposed to be
- RES: always ``True``, terminates DevAssistant if something goes wrong
- LRES: always empty string
- Example::

    dda_run: ${path}/to/project

Logging Commands
----------------

Log commands on various levels. Logging on ERROR or CRITICAL logs the message and then terminates the execution.

``log_[d,i,w,e,c]`` (the letters stand for DEBUG, INFO, WARNING, ERROR, CRITICAL)

- Input: a string, possibly containing variables and references to files
- RES: the logged message (with expanded variables and files)
- LRES: always ``True``
- Example::

    log_i: Hello $name!
    log_e: Yay, something has gone wrong, exiting.

SCL Command
-----------

Run subsection in SCL environment.

``scl [args to scl command]``  (note: you **must** use the scriptlet name - usually ``enable`` -
because it might vary)

- Input: a subsection
- RES: RES of the last command in the given section
- LRES: LRES of the last command in the given section
- Example::

    - scl enable python33 postgresql92: 
      - cl_i: python --version 
      - cl_i: pgsql --version

Use Another Section
-------------------

Runs a section specified by **command input** at this place.

``use``, ``call`` (these two do completely same, ``call`` is obsolete and will be removed in 0.9.0)
This can be used to run:

- another section of this assistant (e.g. ``use: self.run_foo``)
- section of superassistant (e.g. ``use: super.run``) - searches all superassistants
  (parent of this, parent of the parent, etc.) and runs the first found section of given name
- section from snippet (e.g. ``use: snippet_name.run_foo``)

- Input: a string with section name
- RES: RES of the last command in the given section
- LRES: LRES of the last command in the given section
- Example::

    use: self.run_foo
    use: super.run
    use: a_snippet: run_spam
