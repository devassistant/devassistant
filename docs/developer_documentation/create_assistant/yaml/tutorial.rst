.. _tutorial_dsl:

Tutorial: Creating Your Own Assistant in Yaml DSL
=================================================

So you want to create your own assistant? There is nothing easier... They say
that in all tutorials, right?

This tutorial will guide you through the process of creating simple assistants
of :ref:`different roles <assistant_roles_devel>` - Creator, Tweak,
Preparer, Extras.

This tutorial doesn't cover everything. Consult :ref:`dsl_reference`
when you're missing something you really need to achieve. If you think
that DevAssistant misses some functionality that would be useful, open
a bug at https://www.github.com/devassistant/devassistant/issues or send us
a pull request.

.. include:: ../common-rules.txt

.. _creating_yaml_creator:

Creating a Simple Creator
-------------------------

The title says it all. In this section, we will create a "Creator" assistant,
that means an assistant that will take care of kickstarting a new project.
We will write an assistant that creates a project containing a simple Python
script that uses ``argh`` Python module. Let's suppose that we're writing
this assistant for an RPM based system like Fedora, CentOS or RHEL.

To start, we'll create a file hierarchy for our new assistant, say in
``~/programming`` and modify ``DEVASSISTANT_PATH`` accordingly. Luckily,
there is an assistant that does all this - `dap <https://dapi.devassistant.org/dap/dap/>`_::

   da pkg install dap
   da create dap -n ~/programming/pyargh --crt
   export DEVASSISTANT_PATH=~/programming/pyargh/

Running ``da create dap`` scaffolds everything that's needed to create a DAP package
that can be distributed on `DevAssistant Package Index, DAPI <https://dapi.devassistant.org/>`_,
see :ref:`packaging_and_distributing` for more information.

Since this assistant is a "creator", we need to put it somewhere under
``~/programming/assistants/crt/``. Assistants can be organized in a hierarchical
structure, so you could have e.g. ``~/programming/pyargh/assistants/crt/python-scripts.yaml``
as a superassistant and ``~/programming/pyargh/assistants/crt/python-scripts/pyargs.yaml``
as its subassistant, but for this example we'll keep things simple and put ``pyargh.yaml``
directly under ``~/programming/pyargh/assistants/crt/``.

Note, that in pre-0.10.0 DevAssistant versions, it was recommended to hook such assistants
in already existing hierarchies (e.g. using superassistants provided by someone else).
Since 0.10.0, this is no longer recommended. The main reason for this is that we are introducing
a simple upstream packaging and distribution format, as well as "DevAssistant package index" -
a central repository of upstream assistant packages. See :ref:`packaging_and_distributing`
for more details. In this concept, each package can only have one superassistant (named
as the whole package is named) in each ``crt``, ``twk``, ``prep`` and ``extra`` and can only
place subassistants into hierarchies defined by these. Package names have to be unique
in the DevAssistant Package Index.

Setting it Up
~~~~~~~~~~~~~

So, let's start writing ``~/programming/pyargh/assistants/crt/pyargh.yaml`` by providing
some initial metadata::

   fullname: Argh Script Template
   description: Create a template of simple script that uses argh library
   project_type: [python]

If you now save the file and run ``da create pyargh -h``, you'll see that
your assistant was already recognized by DevAssistant, although it doesn't
provide any functionality yet. (Including project type in your Creator assistant
is not necessary, but it may bring some benefits - see :ref:`project_types_ref`.

Dependencies
~~~~~~~~~~~~

Now, we'll want to add a dependency on ``python-argh`` (which is how the
package is called e.g. on Fedora). You can do this just by adding::

   dependencies:
   - rpm: [python-argh]

Now, if you save the file and actually try to run your assistant with
``da create pyargh``, it will install ``python-argh``! (Well, assuming
it's not already installed, in which case it will do nothing.) This is
really super-cool, but the assistant still doesn't do any project setup,
so let's get on with it.

Files
~~~~~

Since we want the script to always look the same, we will create a file that
our assistant will copy into proper place. This file should be put into
into ``crt/pyargh`` subdirectory the files directory
(``~/programming/files/crt/pyargh``). The file will be called
``arghscript.py`` and will have this content::

   #!/usr/bin/python2

   from argh import *

   def main():
       return 'Hello world'

   dispatch_command(main)

We will need to refer to this file from our assistant, so let's open
``argh.yaml`` again and add a ``files`` section::

   files:
     arghs: &arghs
       source: arghscript.py

DevAssistant will automatically search for this file in the correct directory,
that is ``~/programming/files/crt/pyargh``.
If an assistant has more subassistants, e.g. ``crt/pyargh/someassistant`` and
these assistants need to share some files, it is reasonable to place them into
``~/programming/files/crt/pyargh`` and refer to them with relative path like
``../file.foo`` from the subassistants.
Note, that the two ``arghs`` in ``arghs: &arghs`` should be the same because of
`issue 74 <https://github.com/devassistant/devassistant/issues/74>`_.

Run
~~~

Finally, we will be adding a ``run`` section, which is the section that does
all the hard work. A ``run`` section is a list of **commands**. Every command
is in fact a Yaml mapping with exactly one key and value. The key determines
**command type**, while value is the **command input**. For example, ``cl`` is
a **command type** that says that given **input** should be run on commandline,
``log_i`` is a **command type** that lets us print the **input** (message in
this case) for user, etc.

Let's start writing our ``run`` section::

   run:
   - log_i: Hello, I'm Argh assistant and I will create an argh project for you.

But wait! We don't know what the project should be called and where it
should be placed... Before we finish the ``run`` section, we'll need to add
some arguments to our assistant.

Oh Wait, Arguments!
~~~~~~~~~~~~~~~~~~~

Creating any type of project typically requires some user input, at least name
of the project to be created. To ask user for this sort of information, we can
use DevAssistant arguments like this::

   args:
     name:
       flags: [-n, --name]
       required: True
       help: 'Name of project to create'

This means that this assistant will have one argument called ``name``. On
commandline, it will expect ``-n foo`` or ``--name foo`` and since the
argument is required, it will refuse to run without it.

You can now try running ``da create pyargh -h`` and you'll see that the
argument is printed out in commandline help.

Since there are some common arguments that the standard installation of
DevAssistant ships with so called "snippets", that contain (among other
things) definitions of frequentyl used arguments. You can use name argument
for Creator assistants like this::

   args:
     name:
       use: common_args

See :ref:`common_assistant_behaviour` for more information.

Run Again
~~~~~~~~~

Now that we're able to obtain project name (let's assume that it's an arbitrary
path to a directory where the argh script should be placed), we can continue.
First, we will make sure that the directory doesn't already exist. If so,
we need to exit, because we don't want to overwrite or break something::

   run:
   - log_i: Hello, I'm Argh assistant and I will create an argh project for you.
   - if $(test -e "$name"):
     - log_e: '"$name" already exists, can't proceed.'

There are few things to note here:

- There is a simple ``if`` condition with a shell command. If the shell command
  returns a non-zero value, the condition will evaluate to false, else it will
  evaluate to true. So in this case, if something exists at path ``"$name"``,
  the condition will evaluate to true.
- In any command, we can use value of the ``name`` argument by prefixing
  argument name with ``$`` (so  ``$name`` or ``${name}``).
- The ``log_e`` command type is used to print a message and then abort the
  assistant execution immediately.

Let's continue by creating the directory. Add this line to ``run`` section::

   - cl: mkdir -p "$name"

You may be wondering what will happen, if DevAssistant doesn't have write
permissions or more generally if the ``mkdir`` command just fails. In this
case, DevAssistant will exit, printing the output of failed command for user.

Next, we want to copy our script into the directory. We want to name it the
same as name of the directory itself. But what if directory is a path, not
simple name? We have to find out the project name and remember it somehow::

   - $proj_name~: $(basename "$name")

What just happened? We assigned output of command ``basename "$name"`` to
a new variable ``proj_name`` that we can use from now on. Note the ``~`` at the end
of ``$proj_name~``. This is called **execution flag** and it says that the command input
should be executed as an expression, not taken as a literal. See :ref:`expressions_ref`
for detailed expressions reference and :ref:`variables_ctxt_ref` to find out more
about variables.

*Note: the execution flag makes DevAssistant execute the input as a so-called "execution
section". The input can either be a string, evaluated as an expression, or a list of commands,
evaluated as another "run" section.*

So let's copy the script and make it executable::

   - cl: cp *arghs ${name}/${proj_name}.py
   - cl: chmod +x ${name}/${proj_name}.py

One more thing to note here: by using ``*arghs``, we reference a file
from the ``files`` section.

Now, we'll use a super-special command::

   - dda_c: "$name"

What is ``dda_c``? The first part, ``dda`` stands for "dot devassistant file",
the second part, ``_c``, says, that we want to create this file (there are
more things that can be done with ``.devassistant`` file, see :ref:`dda_commands_ref`).
The "command" part of this call just says where the file should be stored,
which is directory ``$name`` in our case.

The ``.devassistant`` file serves for storing meta information about the
project. Amongst other things, it stores information about which assistant was
invoked. This information can later serve to prepare the environment (e.g.
install ``python-argh``) on another machine. Assuming that we commit the
project to a git repository, one just needs to run
``da prepare custom -u <repo_url>``, and DevAssistant will checkout the project
from git and use information stored in ``.devassistant`` to reinstall
dependencies. (There is more to this, you can for example add a custom
``run`` section to ``.devassistant`` file or add custom dependencies,
but this is not covered by this tutorial (see :ref:`dot_devassistant_ref`).

*Note: There can be more dependencies sections and run sections in one
assistant. To find out more about the rules of when they're used and how
run sections can call each other, consult*
:ref:`dependencies reference <dependencies_ref>` *and*
:ref:`run reference <run_sections_ref>`.

Something About Snippets
~~~~~~~~~~~~~~~~~~~~~~~~

Wait, did we say Git? Wouldn't it be nice if we could setup a Git repository
inside the project directory and do an initial commit? These things are always
the same, which is exactly the type of task that DevAssistant should do for
you.

Previously, we've seen usage of argument from snippet. But what if you could
use a part of ``run`` section from there? Well, you can. And you're lucky,
since there is a snippet called ``git.init_add_commit``, which does exactly
what we need. This snippet can be found in the `git <https://dapi.devassistant.org/dap/git/>`_
DAP. During development, you can install ``git`` DAP using ``da pkg install git``.
For runtime, you'll need to add it as dependency to ``meta.yaml`` - see
:ref:`meta_yaml_ref` for more info on dependencies.
We'll use the snippet like this::

   - cl: cd "$name"
   - use: git.init_add_commit.run

This calls section ``run`` from snippet ``git_init_add_commit`` in this place.
Note, that all variables are "global" and the snippet will have access to them
and will be able to change their values. However, variables defined in called
snippet section will not propagate into current section.

Finished!
~~~~~~~~~

It seems that everything is set. It's always nice to print a message that
everything went well, so we'll do that and we're done::

   - log_i: Project "$proj_name" has been created in "$name".

The Whole Assistant
~~~~~~~~~~~~~~~~~~~

... looks like this::

   fullname: Argh Script Template
   description: Create a template of simple script that uses argh library
   project_type: [python]

   dependencies:
   - rpm: [python-argh]

   files:
     arghs: &arghs
       source: arghscript.py

   args:
     name:
       use: common_args

   run:
   - log_i: Hello, I'm Argh assistant and I will create an argh project for you.
   - if $(test -e "$name"):
     - log_e: '"$name" already exists, cannot proceed.'
   - cl: mkdir -p "$name"
   - $proj_name~: $(basename "$name")
   - cl: cp *arghs ${name}/${proj_name}.py
   - cl: chmod +x *arghs ${name}/${proj_name}.py
   - dda_c: "$name"
   - cl: cd "$name"
   - use: git_init_add_commit.run
   - log_i: Project "$proj_name" has been created in "$name".

And can be run like this: ``da create pyargh -n foo/bar``.


Creating a Tweak Assistant
--------------------------

*This section assumes that you've read the previous tutorial and are therefore
familiar with DevAssistant basics.*
Tweak assistants are meant to work with existing projects. They usually try to look
for ``.devassistant`` file of the project, but it is not necessary.

Tweak Assistant Specialties
~~~~~~~~~~~~~~~~~~~~~~~~~~~

**The special behaviour of tweak assistants only applies if you use dda_r in pre_run
section. This command reads .devassistant file from given directory and
puts the read variables in global variable context, so they're available from
all the following dependencies and run section.**

If tweak assistant reads ``.devassistant`` file in ``pre_run`` section, DevAssistant
tries to search for more ``dependencies`` sections to use. If the project was
previously created by ``crt python django``, the engine will install dependencies
from sections ``dependencies_python_django``, ``dependencies_python`` and ``dependencies``.

Also, the engine will try to run ``run_python_django`` section first, then it
will try ``run_python`` and then ``run`` - note, that this will only run the
first found section and then exit, unlike with dependencies, where all found
sections are used.

-- IN PROGRESS --
