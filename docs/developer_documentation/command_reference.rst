.. _command_ref:

Command Reference
=================

This page serves as a reference for commands of the DevAssistant
:ref:`Yaml DSL <create_yaml_assistant>`. These commands
are also callable from :ref:`PingPong scripts <create_pingpong_assistant>`.
Every command consists of a **command_type** and **command_input**. After it gets executed,
it sets the ``LAST_LRES`` and ``LAST_RES`` variables. These are also its return values,
similar to :ref:`expressions_ref` **logical result** and **result**.

- ``LAST_LRES`` is the logical result of the run - ``True``/``False`` if successful/unsuccessful
- ``LAST_RES`` is the "return value" - e.g. a computed value

In the Yaml DSL, commands are called like this::

   - command_type: command_input

This reference summarizes commands included in DevAssistant itself in the following format:

``command_type`` - some optional info

- Input: what should the input look like?
- RES: what is ``LAST_RES`` set to after this command?
- LRES: what is ``LAST_LRES`` set to after this command?
- Example: example usage

Note: if a command explanation says that command "*raises exception*" under some circumstances,
it means that a critical error has occured and assistant execution has to be interrupted
immediately. See documentation for :ref:`exceptions in run sections <run_section_exceptions_ref>`
for details on how this reflects on command line and in GUI. In terms of the underlying Python
source code, this means that ``exceptions.CommandException`` has been raised. Exceptions
can be :ref:`caught <catching_exceptions_ref>`.

*Missing something?* Commands are your entry point for extending DevAssistant.
If you're missing some functionality in ``run`` sections, just
:ref:`write a command runner <command_runners>` and either
:ref:`include it with your assistant <load_cmd_command_ref>` or send us a pull request
to get it merged in DevAssistant core.

Builtin Commands
----------------

There are three builtin commands that are inherent part of DevAssistant Yaml DSL:

- variable assignment
- condition
- loop

All of these builtin commands utilize expressions in some way - these must follow rules in
:ref:`expressions_ref`.

.. _variable_assignment_ref:

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

   - $foo: "bar"
   - $spam:
     - spam
     - spam
     - spam
   - $bar: $baz
   - $success, $list~: $(ls "$foo")

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

   - if defined $foo:
     - log_i: Foo is $foo!
   - else:
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

   - for $i word_in $(ls):
     - log_i: File: $i

   - $foo:
       1: one
       2: two
   - for $k, $v in $foo:
     - log_i: $k, $v

.. _catching_exceptions_ref:

Catching Exceptions
~~~~~~~~~~~~~~~~~~~

Catching runtime exceptions.

``catch $was_exc, $exc`` - execute passed subsection, catch exception if raised. ``$was_exc``
contains ``True`` if exception was raised, ``False`` otherwise; ``$exc`` contains string
representation of exception if one was raised, else it's empty string.

- Input: a subsection to execute and catch exception for
- RES: string representation of exception if one was raised, empty string otherwise
- LRES: ``True`` if exception was raised, ``False`` otherwise
- Example::

   - catch $was_exc, $exc:
     - cl: ls something_that_doesn_exist

   - if $was_exc:
     # handle exception

Note that ``$exc`` may theoretically be empty string even if an exception was raised
(an example of that is running ``cl: false``, which fails without output). It is therefore
important to use ``$was_exc`` variable to determine whether an exception was raised.

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

- Input: mapping containing ``prompt`` (short prompt for user)

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


.. _cl_command_ref:

Command Line Commands
---------------------

Run commands in subprocesses and receive their output.

``cl``, ``cl_[i,r]`` (these do the same, but appending ``i`` logs the command output on INFO level
and appending ``r`` runs command as root; appending ``p`` makes DevAssistant pass subcommand error,
e.g. execution continues normally even if subcommand return code is non-zero)

- Input: a string, possibly containing variables and references to files
- RES: stdout + stdin interleaved as they were returned by the executed process
- LRES: always ``True``, *raises exception* on non-zero return code
- Example::

   - cl: mkdir ${name}
   - cl: cp *file ${name}/foo
   - cl_i: echo "Hey!"
   - cl_ir: echo "Echoing this as root"
   - cl_r: mkdir /var/lib/foo
   - $lres, $res:
     - cl_ip: cmd -this -will -log -in -realtime -and -save -lres -and -res -and -then -continue

If you need to set environment variables for multiple subsequent commands, consult
:ref:`env_command_ref`.

Note: when using ``r``, it's job of DevAssistant core to figure out what to use as authentication
method. Consider this an implementation detail.

*A note on changing current working directory: Due to the way Python interpreter works,
DevAssistant has to specialcase "cd <dir>" command, since it needs to call a special Python
method for changing current working directory of the running interpreter. Therefore you
must always use "cd <dir>" as a single command (do not use "ls foo && cd foo");
also, using pushd/popd is not supported for now.*

.. _env_command_ref:

Modifying Subprocess Environment Variables
------------------------------------------

Globaly set/unset shell variables for subprocesses invoked by :ref:`cl_command_ref`
and in :ref:`expressions_ref`.

``env_set``, ``env_unset``

- Input: a mapping of variables to set if using ``env_set``, name (string) or names (list)
  of variables to unset if using ``env_unset``
- RES: mapping of newly set variable name(s) to their new values (for ``env_set``)
  or unset variables to their last values (for ``env_unset``)
- LRES: always ``True``
- Example::

   - env_set:
       FOO: bar
   # If FOO is not in local DevAssistant context, DevAssistant does no substitution.
   #  This measn that the shell still gets "echo $FOO" to execute and prints "bar".
   - cl_i: echo $FOO
   - env_unset: FOO

Note: If some variables to be unset are not defined, their names are just ignored.

.. _dependencies_command_ref:

Dependencies Command
--------------------

Install dependencies from given **command input**.

``dependencies``

- Input: list of mappings, similar to :ref:`Dependencies section <dependencies_ref>`, but without
  conditions and usage of sections from snippets etc.
- RES: **command input**, but with expanded variables
- LRES: always ``True`` if everything is ok, *raises exception* otherwise
- Example::

   - if $foo:
     - $rpmdeps: [foo, bar]
   - else:
     - $rpmdeps: []

   - dependencies:
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

   - dda_c: ${path}/to/project

``dda_r`` - reads an existing ``.devassistant`` file, should be used by tweak and preparer
assistants.Sets some global variables accordingly, most importantly ``original_kwargs`` (arguments
used when the project was created) - these are also made available with ``dda__`` prefix (yes,
that's double underscore).

- Input: directory where the file is supposed to be
- RES: always empty string
- LRES: ``True``, *raises exception* if something goes wrong
- Example::

   - dda_r: ${path}/to/project

``dda_w`` - writes a mapping (dict in Python terms) to ``.devassistant``

- Input: mapping with two elements:
    1) ``path``: The directory name containing the ``.devassistant`` file
    2) ``write``: Mapping with values to write
- Variables in the ``write`` mapping will be substituted, you have to use
  ``$$foo`` (two dollars instead of one) to get them as variables in ``.devassistant``.
- RES: always empty string
- LRES: ``True``, *raises exception* if something goes wrong
- Example::

   - dda_w:
       path: ${path}/to/project
       write:
         run:
         - $$foo: $name # name will get substituted from current variable
         - log_i: $$foo

**Note: The input for the dda_w command can also be in the form of a list
with two items: the directory name, and the mapping with values to write. This
way is discouraged and will be deprecated**

``dda_dependencies`` - installs dependencies from ``.devassistant`` file, should be used by
preparer assistants. Utilizes both dependencies of creator assistants that created this project
plus dependencies from ``dependencies`` section, if present (this section is evaluated in the
context of current assistant, not the creator).

- Input: directory where the file is supposed to be
- RES: always empty string
- LRES: ``True``, *raises exception* if something goes wrong
- Example::

   - dda_dependencies: ${path}/to/project

``dda_run`` - run ``run`` section from from ``.devassistant`` file, should be used by
preparer assistants. This section is evaluated in the context of current assistant, not the
creator.

- Input: directory where the file is supposed to be
- RES: always empty string
- LRES: ``True``, *raises exception* if something goes wrong
- Example::

   - dda_run: ${path}/to/project

Github Command
--------------

Manipulate Github repositories. Two factor authentication is supported out of
the box.

Github command (``github``) has many "subcommands". Subcommands are part of the command input,
see below.

- Input: a string with a subcommand or a mapping, containing these items:
    1) ``do``: Name of the subcommand to run (see below)
    2) Other parameters for the subcommand
- RES: if command succeeds, either a string with URL of manipulated repo or empty string is
  returned (depends on subcommand), else a string with problem description (it is already logged
  at WARNING level)
- LRES: ``True`` if the Github operation succeeds, ``False`` otherwise
- Example::

   - github:
       do: create_repo
       login: $ghlogin
       reponame: $reponame

   - github:
       do: create_and_push
       login: bkabrda
       reponame: devassistant

   - github: push

   - github:
       do: create_fork
       repo_url: $repo_url
       login: $reponame

**Note: The input for the github command can also be in the form of a list
with two items: the subcommand name, and the mapping with values to use. This
way is discouraged and will be deprecated**

Explanation of individual subcommands follows. Each subcommand takes defined arguments.
E.g. ``create_and_push`` takes an argument ``login``.

``create_repo``
  Creates a repo with given ``reponame`` for a user with given login.
  If no or empty login is specified, local username is used.
  Optionally accepts ``private`` argument to create repo as private.

``create_and_push``
  Same as ``create_repo``, but it also adds a proper git remote to repository in current
  working dir and pushes to Github.

``push``
  Just does ``git push -u origin master``, no arguments needed.

``create_fork``
  Creates a fork of repo at given ``repo_url`` under user specified by ``login``.

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
- LRES: ``True``, *raises exception* if something goes wrong
- Example::

   - jinja_render:
       template: *somefile
       destination: ${dest}/foo
       overwrite: yes
       output: filename.foo
       data:
         foo: bar
         spam: spam

   - jinja_render_dir:
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

   - log_i: Hello $name!
   - log_e: Yay, something has gone wrong, exiting.

Docker Commands
---------------

Control Docker from assistants.

``docker_[build,cc,start,stop,attach,find_img,container_ip,container_name]``

- Input:

  - ``attach`` - list or string with names/hashes of container(s) (if string is provided,
    it's split on whitespaces to get names/hashes)
  - ``build`` - mapping with arguments same as ``build`` method from docker_py_api_,
    but ``path`` is required and ``fileobj`` is ignored
  - ``cc`` - mapping with arguments same as ``create_container`` method from
    docker_py_api_, ``image`` is required
  - ``container_ip`` - string (container hash/name)
  - ``container_name`` - string (container hash)
  - ``find_img`` - string (a start of hash of image to find)
  - ``start`` - mapping with arguments same as ``start`` method from docker_py_api_,
    ``container`` is required
  - ``stop`` - mapping with arguments same as ``stop`` method from docker_py_api_,
    ``container`` is required

- LRES and RES:

  - ``attach`` - LRES is ``True`` if all attached containers end with success, ``False``
    otherwise; RES is always a string composed of outputs of all containers
  - ``build`` - ``True`` and hash of built image on success, otherwise *raises exception*
  - ``cc`` - ``True`` and hash of created container, otherwise *raises exception*
  - ``container_ip`` - ``True`` and IPv4 container address on success, otherwise
    *raises exception*
  - ``container_name`` - ``True`` and container name on success, otherwise *raises exception*
  - ``find_img`` - ``True`` and image hash on success if there is only one image that starts
    with provided input; ``False`` and string with space separated image hashes if there are
    none or more than one images
  - ``start`` - ``True`` and container hash on success, *raises exception* otherwise
  - ``stop`` - ``True`` and container hash on success, *raises exception* otherwise

- Example (build an image, create container, start it and attach to output; stop it on
  DevAssistant shutdown)::

   run:
   # build image
   - $image~:
     - docker_build:
         path: .
   # create container
   - $container~:
     - docker_cc:
         image: $image
   # start container
   - docker_start:
       container: $container
   - log_i~:
     - docker_container_ip: $container
   # register container to be shutdown on DevAssistant exit
   - atexit:
     - docker_stop:
         container: $container
         timeout: 3
   # attach to container output - this can be interrupted by Ctrl+C in terminal,
   #  but currently not in GUI, see https://github.com/devassistant/devassistant/issues/284
   - docker_attach: $container

.. _docker-py library API: https://github.com/docker/docker-py/#api
.. _docker_py_api: `docker-py library API`_

Vagrant-Docker Commands
-----------------------

Control Docker using Vagrant from assistants.

``vagrant_docker``

- Input: string with vagrant command to run, must start with one of ``up``, ``halt``,
  ``destroy``, ``reload``
- RES: hashes/names of containers from Vagrantfile (not all of these were necessarily
  manipulated with, for example if you use ``halt``, all container hashes are returned
  even if no containers were previously running)
- LRES: ``True``, *raises exception* if something goes wrong
- Example::

   - vagrant_docker: halt
   - vagrant_docker: up

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

``use``
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

This way, the whole context (all variables) are passed into the section run
(by value, so they don't get modified).

Another, more function-like usage is also available::

   - use:
       sect: self.run_foo
       args:
         foo: $bar
         baz: $spam

Using this approach, the assistant/snippet and section name is taken from ``sect`` and 
only arguments listed in ``args`` are passed to the section (plus all "magic" variables,
e.g. those starting and ending with double underscore).

.. _normalize_commands_ref:

Normalizing User Input
----------------------

Replace "weird characters" (whitespace, colons, equals...) by underscores and unicode chars
by their ascii counterparts.

- Input: a string or a mapping containing keys ``what`` and ``ok_chars`` (``ok_chars`` is a string
  containing characters that should not be normalized)
- RES: a string with weird characters (e.g. brackets/braces, whitespace, etc) replaced by underscores
- LRES: True
- Example::

   - $dir~:
     - normalize: foo!@#$%^bar_ěšč
   - cl: mkdir $dir  # creates dir named foo______bar_esc
   - $dir~:
     - normalize:
         what: f-o.o-@#$baz
         ok_chars: "-."
   - cl: mkdir $dir  # creates dir named f-o.o-___baz

Setting up Project Directory
----------------------------

Creates a project directory (possibly with a directory containing it) and sets some global variables.

- Input: a mapping of input options, see below
- RES: path of project directory or a directory containing it, if ``create_topdir`` is ``False``
- LRES: ``True``, *raises exception* if something goes wrong
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
- ``normalize_ok_chars`` - string containing characters that should not be normalized,
  assuming that ``create_topdir: normalized`` is used
- ``contdir_var``, ``topdir_var``, ``topdir_normalized_var`` - names to which the global
  variables should be assigned to - *note: you have to use variable names without dollar sign here*
- ``accept_path`` - either ``True`` (default) or ``False`` - if ``False``, this will terminate
  DevAssistant if a path is provided
- ``on_existing`` - one of ``fail`` (default), ``pass`` - if ``fail``, this will terminate
  DevAssistant if directory specified by ``from`` already exists; if ``pass``, nothing will
  happen; note, that this is always considered ``pass``, if ``create_topdir`` is ``False``
  (in which case the assistant is in full control and responsible for checking everything itself)

.. _run_atexit_ref:

Running Commands After Assistant Exits
--------------------------------------

Register commands to be run when assistant exits (this is not necessarily DevAssistant exit).

- Input: section (list of commands to run)
- RES: the passed list of commands (raw, unformatted)
- LRES: True
- Example::

   - $server: $(get server pid)
   - atexit:
     - cl: kill $server
     - log_i: Server gets killed even if the assistant failed at some point.'

Sections registered by ``atexit`` are run at the very end of assistant execution
even after the ``post_run`` section. There are some differencies compared to ``post_run``:

- ``atexit`` command creates a "closure", meaning the values of variables in time of
  the actual section invocation are the same as they were at the time the ``atexit`` command
  was used (meaning that even if you change variable values during the ``run`` section after
  running ``atexit``, the values are preserved).
- You can use multiple ``atexit`` command calls to register multiple sections. These are run
  in the order in which they were registered.
- Even if some of the sections registered with ``atexit`` fail, the others are still invoked.

.. _pingpong_command_ref:

DevAssistant PingPong
---------------------

Run :ref:`DevAssistant PingPong scripts <create_pingpong_assistant>`.

- Input: a string to line on commandlie
- RES: Result computed by the PingPong script
- LRES: Logical result computed by the PingPong script
- Example::

   - pingpong: python3 *file_from_files_section

.. _load_cmd_command_ref:

Loading Custom Command Runners
------------------------------

Load DevAssistant :ref:`command runner(s) <command_runners>` from a file.

- Input: string or mapping, see below
- RES: List of classnames of loaded command runners
- LRES: True if at least one command runner was loaded, False otherwise
- Example::

   files:
     my_cr: &my_cr
       source: cr.py

   run:
   - load_cmd: *my_cr
   # assuming that there is a command runner that runs "mycommand" in the file,
   #  we can do this as of now until the end of this assistant
   #  this is equivalent of
   #  - load_cmd:
   #      from_file: *my_cr
   - mycommand: foo

   # load command runner from file provided in hierarchy of a different assistant
   # - make it prefixed to make sure it doesn't conflict with any core command runners
   # - load only BlahCommandRunner even if the file includes more runners
   - load_cmd:
       from_file: crt/someotherassistant/crs.py
       prefix: foo
       only: BlahCommandRunner
   - foo.blah: input  # runs ok
   - blah: input  # will fail, the command runner was registered with "foo" prefix

Note: since command runners loaded by ``load_cmd`` have higher priority than DevAssistant
builtin command runners, you can use this to *override* the builtins. E.g. you can have
a command runner that overrides ``log_i``. If someone wants to use this command runner
of yours but also keep the original one, he can provide a ``prefix``, so that your logging
command is only available as ``some_prefix.log_i``.
