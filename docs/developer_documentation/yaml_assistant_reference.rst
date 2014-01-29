.. _assistants in our Github repo: https://github.com/bkabrda/devassistant/tree/master/devassistant/assistants/assistants

.. _yaml_assistant_reference:

Yaml Assistant Reference
========================

*When developing assistants, please make sure that you read proper version
of documentation. The Yaml DSL of devassistant is still evolving rapidly,
so consider yourself warned.*

This is a reference manual to writing yaml assistants. Yaml assistants
use a special DSL defined on this page. For real examples, have a look
at `assistants in our Github repo`_.

*Why the hell another DSL?*
  When we started creating DevAssistant and we were asking people who
  work in various languages whether they'd consider contributing assistants
  for those languages, we hit the "I'm not touching Python" barrier. Since
  we wanted to keep the assistants consistent (centralized logging, sharing
  common functionality, same backtraces, etc...), we created a new DSL.
  So now we have something that everyone complains about, including Pythonists,
  which seems to be consistent too ;)

Assistant Roles
---------------

For list and description of assistant roles see :ref:`assistant_roles_devel`.

The role is implied by assistant location in one of the load path directories,
as mentioned in :ref:`assistants_loading_mechanism`.

All the rules mentioned in this document apply to all types of assistants,
with exception of sections :ref:`modifier_assistants_ref`, :ref:`preparer_assistants_ref` and
:ref:`task_assistants_ref` that talk about specifics of Modifier, resp. Preparer, resp. Task
assistants.

Assistant Name
--------------

Assistant name is a short name used on command line, e.g. ``python``. It
should also be the only top-level yaml mapping in the file (that means
just one assistant per file). Each assistant should be placed in a file
that's named the same as the assistant itself (e.g. ``python`` assistant
in ``python.yaml`` file).

Assistant Content
-----------------

The top level mapping has to be mapping from assistant name to assistant
attributes, for example::

   python:
     fullname: Python
     # etc.

List of allowed attributes follows (all of them are optional, and have some
sort of reasonable default, it's up to your consideration which of them to use):

``fullname``
  a verbose name that will be displayed to user (``Python Assistant``)
``description``
  a (verbose) description to show to user (``Bla bla create project bla bla``)
``dependencies`` (and ``dependencies_*``)
  specification of dependencies, see below `Dependencies`_
``args``
  specification of arguments, see below `Args`_
``files``
  specification of used files, see below `Files`_
``run`` (and ``run_*``)
  specification of actual operations, see below `Run`_
``files_dir``
  directory where to take files (templates, helper scripts, ...) from. Defaults
  to base directory from where this assistant is taken + ``files``. E.g. if
  this assistant is ``~/.devassistant/assistants/crt/path/and/more.yaml``,
  files will be taken from ``~/.devassistant/files/crt/path/and/more`` by default.
``icon_path``
  absolute or relative path to icon of this assistant (will be used by GUI).
  If not present, a default path will be used - this is derived from absolute
  assistant path by replacing ``assistants`` by ``icons`` and ``.yaml`` by
  ``.svg`` - e.g. for ``~/.devassistant/assistants/crt/foo/bar.yaml``,
  the default icon path is ``~/.devassistant/icons/crt/foo/bar.svg``

Assistants Invocation
---------------------

When you invoke DevAssistant with it will run following assistants sections in following order:

- ``pre_run``
- ``dependencies``
- ``run`` (possibly different section for `Modifier Assistants`_)
- ``post_run``

If any of the first three sections fails in any step, DevAssistant will immediately skip to
``post_run`` and the whole invocation will be considered as failed (will return non-zero code
on command line and show "Failed" in GUI).

.. _dependencies_ref:

Dependencies
------------

Yaml assistants can express their dependencies in multiple sections.

- Packages from section ``dependencies`` are **always** installed.
- If there is a section named ``dependencies_foo``, then dependencies from this section are installed
  **iff** ``foo`` argument is used (either via commandline or via gui). For example::

   $ da python --foo

- These rules differ for `Modifier Assistants`_

Each section contains a list of mappings ``dependency type: [list, of, deps]``.
If you provide more mappings like this::

   dependencies:
   - rpm: [foo]
   - rpm: ["@bar"]

they will be traversed and installed one by one. Supported dependency types: 

``rpm``
  the dependency list can contain RPM packages or YUM groups
  (groups must begin with ``@`` and be quoted, e.g. ``"@Group name"``)
``use`` / ``call`` (these two do completely same, ``call`` is obsolete and will be removed in 0.9.0)
  installs dependencies from snippet/another dependency section of this assistant/dependency
  section of superassistant. For example::

   dependencies:
   - use: foo # will install dependencies from snippet "foo", section "dependencies"
   - use: foo.dependencies_bar # will install dependencies from snippet "foo", section "bar"
   - use: self.dependencies_baz # will install dependencies from section "dependencies_baz" of this assistant
   - use: super.dependencies # will install dependencies from "dependencies" section of first superassistant that has such section

``if``, ``else``
  conditional dependency installation. For more info on conditions, `Run`_ below.
  A very simple example::

   dependencies:
   - if $foo:
     - rpm: [bar]
   - else:
     - rpm: [spam]

Full example::

   dependencies: - rpm: [foo, "@bar"]

   dependencies_spam:
   - rpm: [beans, eggs]
   - if $with_spam:
     - use: spam.spamspam
   - rpm: ["ham${more_ham}"]

*Sometimes your dependencies may get terribly complex - they depend on many
parameters, you need to use them dynamically during ``run``, etc. In these
cases, it is better to use ``dependencies`` command in ``run`` section.*

Args
----

Arguments are used for specifying commandline arguments or gui inputs.
Every assistant can have zero to multiple arguments.

The ``args`` section of each yaml assistant is a mapping of arguments to
their attributes::

   args:
     name:
       flags:
       - -n
       - --name
     help: Name of the project to create.
 
Available argument attributes:

``flags``
  specifies commandline flags to use for this argument. The longer flag
  (without the ``--``, e.g. ``name`` from ``--name``) will hold the specified
  commandline/gui value during ``run`` section, e.g. will be accessible as ``$name``.
``help``
  a help string
``required``
  one of ``{true,false}`` - is this argument required?
``nargs``
  how many parameters this argument accepts, one of ``{0, ?,*,+}``
  (e.g. {0, 0 or 1, 0 or more, 1 or more})
``default``
  a default value (this will cause the default value to be
  set even if the parameter wasn't used by user)
``action``
  one of ``{store_true, [default_iff_used, value]}`` - the ``store_true`` value
  will create a switch from the argument, so it won't accept any
  parameters; the ``[default_iff_used, value]`` will cause the argument to
  be set to default value ``value`` **iff** it was used without parameters
  (if it wasn't used, it won't be defined at all)
``use`` / ``snippet`` (these two do completely same, ``snippet`` is obsolete and will be removed in 0.9.0)
  name of the snippet to load this argument from; any other specified attributes
  will override those from the snippet By convention, some arguments
  should be common to all or most of the assistants.
  See :ref:`common_assistant_behaviour`

Gui Hints
~~~~~~~~~

GUI needs to work with arguments dynamically, choose proper widgets and offer
sensible default values to user. These are not always automatically
retrieveable from arguments that suffice for commandline. For example, GUI
cannot meaningfully prefill argument that says it "defaults to current working
directory". Also, it cannot tell whether to choose a widget for path (with the
"Browse ..." button) or just a plain text field.

Because of that, each argument can have ``gui_hints`` attribute.
This can specify that this argument is of certain type (path/str/bool) and
has a certain default. If not specified in ``gui_hints``, the default is
taken from the argument itself, if not even there, a sensible "empty" default
value is used (home directory/empty string/false). For example::

   args:
     path:
       flags:
       - [-p, --path]
       gui_hints:
         type: path
         default: $(pwd)/foo

If you want your assistant to work properly with GUI, it is good to use
``gui_hints`` (currently, it only makes sense to use it for ``path``
attributes, as ``str`` and ``bool`` get proper widgets and default values
automatically).

Files
-----

This section serves as a list of aliases of files stored in one of the
``files`` dirs of DevAssistant. E.g. if your assistant is
``assistants/crt/foo/bar.yaml``, then files are taken relative to
``files/crt/foo/bar/`` directory. So if you have a file
``files/crt/foo/bar/spam``, you can use::

   files:
     spam: &spam
       source: spam

This will allow you to reference the ``spam`` file in ``run`` section as
``*spam`` without having to know where exactly it is located in your
installation of DevAssistant.


.. _run_ref:

Run
---

Run sections are the essence of DevAssistant. They are responsible for
preforming all the tasks and actions to set up the environment and
the project itself. For Creator and Preparer assistants, section named ``run``
is always invoked, `Modifier Assistants`_ may invoke different sections
based on metadata in ``.devassistant`` file.

Note, that ``pre_run`` and ``post_run`` follow the same rules as ``run`` sections.
See `Assistants Invocation`_ to find out how these sections are invoked.

Every ``run`` section is a sequence of various **commands**, mostly
invocations of commandline. Each command is a mapping
of **command type** to **command input**::

   run:
   - cl: cp foo bar/baz
   - log_i: Done copying.

During the execution, you may use logging (messages will be printed to
terminal or gui) with following levels: ``DEBUG``, ``INFO``, ``WARNING``,
``ERROR``, ``CRITICAL``. By default, messages of level ``INFO`` and higher
are logged. As you can see below, there is a separate ``log_*`` **command**
type for logging, but some other command types also log various messages.
Log messages with levels ``ERROR`` and ``CRITICAL`` terminate execution of
DevAssistant imediatelly.

Run sections allow you to use variables with certain rules and
limitations. See below.

List of supported **commands** can be found at :ref:`command_ref`.

Variables
~~~~~~~~~

Initially, variables are populated with values of arguments from
commandline/gui and there are no other variables defined for creator
assistants. For modifier assistants global variables are prepopulated
with some values read from ``.devassistant``. You can either define
(and assign to) your own variables or change the values of current ones.

Additionally, after each command, variables ``$LAST_RES`` and ``$LAST_LRES`` are populated
with result of the last command - see :ref:`command_ref`

The variable scope works as follows:

- When invoking ``run`` section (from the current assistant or snippet),
  the variables get passed by value (e.g. they don't get modified for the
  remainder of this scope).
- As you would probably expect, variables that get modified in ``if`` and
  ``else`` sections are modified until the end of the current scope.

All variables are global in the sense that if you call a snippet or another
section, it can see all the arguments that are defined.

.. _expressions_ref:

Expressions
~~~~~~~~~~~

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

    - *logical result*: ``True`` **iff** value is not empty and it is not
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


Quoting
~~~~~~~

When using variables that contain user input, they should always be
quoted in the places where they are used for bash execution. That
includes ``cl*`` commands, conditions that use bash return values and
variable assignment that uses bash.

.. _modifier_assistants_ref:

Modifier Assistants
-------------------

Modifier assistants are assistants that are supposed to work with
already created project. They must be placed under ``mod``
subdirectory of one of the load paths, as mentioned in
:ref:`assistants_loading_mechanism`.

There are few special things about modifier assistants:

- They usually utilize ``dda_r`` to read the whole ``.devassistant`` file (usually from directory
  specified by ``path`` variable or from current directory). **Since version 0.8.0, every modifier
  assistant has to do this on its own, be it in pre_run or run section**. This also allows you
  to modify non-devassistant projects - just don't use ``dda_r``.

The special rules below **only apply if you use dda_t in pre_run section**.

- They use dependency sections according to the normal rules + they use *all*
  the sections that are named according to loaded ``$subassistant_path``,
  e.g. if ``$subassistant_path`` is ``[foo, bar]``, dependency sections
  ``dependencies``, ``dependencies_foo`` and ``dependencies_foo_bar`` will
  be used as well as any sections that would get installed according to
  specified parameters. The rationale behind this is, that if you have e.g.
  ``eclipse`` modifier that should work for both ``python django`` and
  ``python flask`` projects, chance is that they have some common dependencies,
  e.g. ``eclipse-pydev``. So you can just place these common dependencies in
  ``dependencies_python`` and you're done (you can possibly place special
  per-framework dependencies into e.g. ``dependencies_python_django``).
- By default, they don't use ``run`` section. Assuming that ``$subassistant_path``
  is ``[foo, bar]``, they first try to find ``run_foo_bar``, then ``run_foo``
  and then just ``run``. The first found is used. If you however use cli/gui
  parameter ``spam`` and section ``run_spam`` is present, then this is run instead.

.. _preparer_assistants_ref:

Preparer Assistants
-------------------

Preparer assistants are assistants that are supposed to checkout sources of upstream
projects and set up environment for them (possibly utilizing their ``.devassistant`` file,
if they have one). Preparers must be placed under ``prep`` subdirectory of one of the load
paths, as mentioned in :ref:`assistants_loading_mechanism`.

Preparer assistants commonly utilize the ``dda_dependencies`` and ``dda_run``
commands in ``run`` section.

.. _task_assistants_ref:

Task Assistants
---------------

Task assistants are supposed to carry out arbitrary task that are not related to a specific
project. <TODO>
