.. _command_ref:

Command Reference
=================

This page serves as a reference for commands of the DevAssistant Yaml DSL.
Every command consists of a **command_type** and **command_input**. After it gets executed,
it sets the ``LAST_LRES`` and ``LAST_RES`` variables. These are also its return values,
similar to :ref:`expressions_ref` **logical result** and **result**.

- ``LAST_LRES`` is the logical result of the run - ``True``/``False`` if successful/unsuccessful
- ``LAST_RES`` is the "return value" - e.g. a computed value

In the Yaml DSL, commands are called like this::

   command_type: command_input

This reference summarizes commands included in DevAssistant itself in the following format:

``command_type`` - some optional info

- Input: what should the input look like?
- RES: what is ``LAST_RES`` set to after this command?
- LRES: what is ``LAST_LRES`` set to after this command?
- Example: example usage

*Missing something?* Commands are your entry point for extending DevAssistant.
If you're missing some functionality in ``run`` sections, just
:ref:`write a command runner <command_runners>` and send us a pull request.

Builtin Commands
----------------

There are three builtin commands that are inherent part of DevAssistant Yaml DSL:

- variable assignment
- condition
- loop

All of these builtin commands utilize expressions in some way - these must follow rules in
:ref:`expressions_ref`.


Variable Assignment
~~~~~~~~~~~~~~~~~~~

Assign *result* (and possibly also *logical result*) of :ref:`expressions_ref`
to a variable(s).

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
    $success, $list~: $(ls "$foo")

Condition
~~~~~~~~~

Conditional execution.

``if <expression>``, ``else`` - conditionally execute one or the other section (``if`` can
stand alone, of course)

- Input: a subsection to run
- RES: RES of last command in the subsection, if this clause is invoked. If not invoked,
  RES remains untouched.
- LRES: LRES of last command in the subsection, if this clause is invoked. If not invoked,
  LRES remains untouched.
- Example::

    if defined $foo:
    - log_i: Foo is $foo!
    else:
    - log_i: Foo is not defined!

Loop
~~~~

A simple for loop.

``for <var>[, <var>] [word_in,in] <expression>`` - loop over result of the expression. If
``word_in`` is used and ``<expression>`` is a string, it will be split on whitespaces and
iterated over; with ``in``, string will be split to single characters and iterated over.
For iterations over lists and mappings, ``word_in`` and ``in`` behave the same. When iterating
over mapping, two control variables may be provided to get both key and its value.

- Input: a subsection to repeat in loop
- RES: RES of last command of last iteration in the subsection. If there are no interations,
  RES is untouched.
- LRES: LRES of last command of last iteration in the subsection. If there are no interations,
  RES remains untouched.
- Example::

     for $i word_in $(ls):
     - log_i: File: $i

     $foo:
       1: one
       2: two
     for $k, $v in $foo:
     - log_i: $k, $v


Ask Commands
------------

User interaction commands, let you ask for password and various other input.

``ask_confirm``

- Input: mapping containing ``prompt`` (short prompt for user) and ``message``
  (a longer description of what the user should confirm)

- RES: the confirmation (``True`` or ``False``)
- LRES: same as RES
- Example::

    - $confirmed~:
      - ask_confirm:
          message: "Do you think DevAssistant is great?"
          prompt: "Please select yes."

``ask_input``

- Input: mapping containing ``prompt`` (short prompt for user) and optionally ``message``
  (a longer description)

- RES: the string that was entered by the user
- LRES: ``True`` if non-empty string was provided
- Example::

     - $variable:
       - ask_input:
           prompt: "Your name"

``ask_password``

- Input: mapping containing ``prompt`` (short prompt for user)
- This command works the same way as ``ask_input``, but the entered text is
  hidden (displayed as bullets)

- RES: the password
- LRES: ``True`` if non-empty password was provided
- Example::

     - $passwd:
       - ask_password:
           prompt: "Please provide your password"


Command Line Commands
---------------------

Run commands in subprocesses and receive their output.

``cl``, ``cl_[i,r]`` (these do the same, but appending ``i`` logs the command output on INFO level
and appending ``r`` runs command as root; appending ``p`` makes DevAssistant pass subcommand error,
e.g. execution continues normally even if subcommand return code is non-zero)

- Input: a string, possibly containing variables and references to files
- RES: stdout + stdin interleaved as they were returned by the executed process
- LRES: always ``True`` (if the command fails, the whole DevAssistant execution fails)
- Example::

    cl: mkdir ${name}
    cl: cp *file ${name}/foo
    cl_i: echo "Hey!"
    cl_ir: echo "Echoing this as root"
    cl_r: mkdir /var/lib/foo
    $lres, $res:
    - cl_ip: cmd -this -will -log -in -realtime -and -save -lres -and -res -and -then -continue

Note: when using ``r``, it's job of DevAssistant core to figure out what to use as authentication
method. Consider this an implementation detail.

*A note on changing current working directory: Due to the way Python interpreter works,
DevAssistant has to specialcase "cd <dir>" command, since it needs to call a special Python
method for changing current working directory of the running interpreter. Therefore you
must always use "cd <dir>" as a single command (do not use "ls foo && cd foo");
also, using pushd/popd is not supported for now.*

.. _dependencies_command_ref:

Dependencies Command
--------------------

Install dependencies from given **command input**.

``dependencies``

- Input: list of mappings, similar to :ref:`Dependencies section <dependencies_ref>`, but without
  conditions and usage of sections from snippets etc.
- RES: **command input**, but with expanded variables
- LRES: always ``True`` (terminates DevAssistant if dependency installation fails)
- Example::

    if $foo:
    - $rpmdeps: [foo, bar]
    else:
    - $rpmdeps: []

    dependencies:
    - rpm: $rpmdeps

.. _dda_commands_ref:

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
- RES: always empty string
- LRES: always ``True``, terminates DevAssistant if something goes wrong
- Example::

    dda_r: ${path}/to/project

``dda_w`` - writes a mapping (dict in Python terms) to ``.devassistant``

- Input: list with directory with ``.devassistant`` file as a first item and the mapping
  to write as the second item. Variables in the mapping will be substituted, you have to use
  ``$$foo`` (two dollars instead of one) to get them as variables in ``.devassistant``.
- RES: always empty string
- LRES: always ``True``, terminates DevAssistant if something goes wrong
- Example::

    dda_w:
    - ${path}/to/project
    - run:
      - $$foo: $name # name will get substituted from current variable
      - log_i: $$foo

``dda_dependencies`` - installs dependencies from ``.devassistant`` file, should be used by
preparer assistants. Utilizes both dependencies of creator assistants that created this project
plus dependencies from ``dependencies`` section, if present (this section is evaluated in the
context of current assistant, not the creator).

- Input: directory where the file is supposed to be
- RES: always empty string
- LRES: always ``True``, terminates DevAssistant if something goes wrong
- Example::

    dda_dependencies: ${path}/to/project

``dda_run`` - run ``run`` section from from ``.devassistant`` file, should be used by
preparer assistants. This section is evaluated in the context of current assistant, not the
creator.

- Input: directory where the file is supposed to be
- RES: always empty string
- LRES: always ``True``, terminates DevAssistant if something goes wrong
- Example::

    dda_run: ${path}/to/project

Github Command
--------------

Manipulate Github repositories.

Github command (``github``) has many "subcommands". Subcommands are part of the command input,
see below.

- Input: a string with a subcommand or a two item list, where the first item is a subcommand
  and the second item is a mapping that explicitly specifies parameters for the subcommand.
- RES: if command succeeds, either a string with URL of manipulated repo or empty string is
  returned (depends on subcommand), else a string with problem description (it is already logged
  at WARNING level)
- LRES: ``True`` if the Github operation succeeds, ``False`` otherwise
- Example::

    github: create_repo

    github:
    - create_and_push
    - login: bkabrda
      reponame: devassistant

    github: push

    github: create_fork

Explanation of individual subcommands follows. Each subcommand takes defined arguments,
whose default values are taken from global context. E.g. ``create_and_push`` takes an argument
``login``. If it is not specified, assistant variable ``github`` is used.

``create_repo``
  Creates a repo with given ``reponame`` (defaults to var ``name``) for a user with
  given login (defaults to var ``github``). Optionally accepts ``private`` argument
  to create repo as private (defaults to var ``github_private``).

``create_and_push``
  Same as ``create_repo``, but it also adds a proper git remote to repository in current
  working dir and pushes to Github.

``push``
  Just does ``git push -u origin master``, no arguments needed.

``create_fork``
  Creates a fork of repo at given ``repo_url`` (defaults ot var ``url``) under user specified
  by ``login`` (defaults to var ``github``).

Jinja2 Render Command
---------------------

Render a Jinja2 template.

``jinja_render``, ``jinja_render_dir`` - render a single template or a directory containing
more templates

- Input: a mapping containing

  - ``template`` - a reference to file (or a directory if using ``jinja_render_dir``)
    in ``files`` section
  - ``destination`` - directory where to place rendered template (or rendered directory)
  - ``data`` - a mapping of values used to render the template itself
  - ``overwrite`` (optional) - overwrite the file if it exists? (defaults to ``false``)
  - ``output`` (optional) - specify a filename of the rendered template (see below for
    information on how the filename is costructed if not provided), not used with
    ``jinja_render_dir``

- RES: always ``success`` string
- LRES: always ``True``, terminates DevAssistant if something goes wrong
- Example::

    jinja_render:
      template: *somefile
      destination: ${dest}/foo
      overwrite: yes
      output: filename.foo
      data:
        foo: bar
        spam: spam

    jinja_render_dir:
      template: *somedir
      destination: ${dest}/somedir
      data:
        foo: foo!
        spam: my_spam

The filename of the rendered template is created in this way (the first step is omitted
with ``jinja_render_dir``:

- if ``output`` is provided, use that as the filename
- else if name of the template endswith ``.tpl``, strip ``.tpl`` and use it
- else use the template name

For template syntax reference, see `Jinja2 documentation <http://jinja.pocoo.org/docs/>`_.

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

.. warning:: If you start your log command with an apostrophe or a quotation mark, you must end the line with the same character, and it must not appear elsewhere on the line

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

Note: currently, this command can't be nested, e.g. you can't run ``scl enable`` in another
``scl enable``.

Running Commands as Another User
--------------------------------

Run subsection as a different user (how this command runner does this is considered
an implementation detail).
``as <username>`` (note: use ``as root``, to run subsection under superuser)

- Input: a subsection
- RES: output of **the whole** subsection
- LRES: LRES of the last command in the given section
- Example::

    - as root:
      - cl: ls /root
    - as joe:
      - log_i~: $(echo "this is run as joe")

Note: This command invokes DevAssistant under another user and passes the whole section to it.
This means some behaviour differences from e.g. ``scl`` command, where each command is run in
current assistant. Most importantly, RES of this command is RES of all commands from given
subsection.

.. _use_commands_ref:

Using Another Section
---------------------

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

    - use: self.run_foo
    - use: super.run
    - use: a_snippet.run_spam

.. _normalize_commands_ref:

Normalizing User Input
----------------------

Replace "weird characters" (whitespace, colons, equals...) by underscores and unicode chars
by their ascii counterparts.

- Input: a string
- RES: a string with weird characters (e.g. brackets/braces, whitespace, etc) replaced by underscores
- LRES: True
- Example::

   - $dir~:
     - normalize: foo!@#$%^bar_ěšč
   - cl: mkdir $dir  # creates dir named foo______bar_esc

Setting up Project Directory
----------------------------

Creates a project directory (possibly with a directory containing it) and sets some global variables.

- Input: a mapping of input options, see below
- RES: path of project directory or a directory containing it, if ``create_topdir`` is ``False``
- LRES: always True, terminates DevAssistant if something goes wrong
- Example::

   - $dir: foo/bar/baz
   - setup_project_dir:
       from: $dir
       create_topdir: normalized

Note: as a side effect, this command runner sets 3 global variables for you (their names can
be altered by using arguments ``contdir_var``, ``topdir_var`` and ``topdir_normalized_var``):

- ``contdir`` - the dir containing project directory (e.g. ``foo/bar`` in the example above)
- ``topdir`` - the project directory (e.g. ``baz`` in the example above)
- ``topdir_normalized`` - normalized name (by :ref:`normalize_commands_ref`) of the
  project directory

Arguments:

- ``from`` (required) - a string or a variable containing string with directory name
  (possibly a path)
- ``create_topdir`` - one of ``True`` (default), ``False``, ``normalized`` - if ``False``,
  only creates the directory containing the project, not the project directory itself
  (e.g. it would create only ``foo/bar`` in example above, but not the ``baz`` directory);
  if ``True``, it also creates the project directory itself; if ``normalized``, it creates
  the project directory itself, but runs it's name through :ref:`normalize_commands_ref` first
- ``contdir_var``, ``topdir_var``, ``topdir_normalized_var`` - names to which the global
  variables should be assigned to - *note: you have to use variable names without dollar sign here*
- ``accept_path`` - either ``True`` (default) or ``False`` - if ``False``, this will terminate
  DevAssistant if a path is provided
- ``on_existing`` - one of ``fail`` (default), ``pass`` - if ``fail``, this will terminate
  DevAssistant if directory specified by ``from`` already exists; if ``pass``, nothing will
  happen; note, that this is always considered ``pass``, if ``create_topdir`` is ``False``
  (in which case the assistant is in full control and responsible for checking everything itself)
