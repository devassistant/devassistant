.. _our issue tracker on Github: https://github.com/bkabrda/devassistant/issues

User Documentation
==================

.. include:: brief-intro.txt

.. _cli_interface:

So What is an Assistant?
------------------------

In short, assistant is a recipe for creating/modifying a project or setting up
environment in a certain way. DevAssistant is in fact just a core that "runs"
assistants according to certain rules.

Each assistant specifies a way how to achieve a single task, e.g. create a new
project in framework X of language Y.

If you want to know more about how this all works, consult
:ref:`yaml_assistant_reference`.

Assistant Roles
~~~~~~~~~~~~~~~

.. include:: assistant-roles.txt

You can learn about how to invoke the
respective roles below in :ref:`creating_projects_cli`,
:ref:`modifying_projects_cli` and :ref:`preparing_environment_cli`.

Using Commandline Interface
---------------------------

.. _creating_projects_cli:

Creating New Projects
~~~~~~~~~~~~~~~~~~~~~

DevAssistant can help you create (that's the ``crt`` in the below command) your
projects with one line in terminal. For example::

   $ da crt python django -n foo -e -g

``da`` is short form of ``devassistant``. You can use any of them, but ``da`` is preferred.

This line will do the following:

- Install Django (RPM packaged) and all needed dependencies.
- Create a Django project named ``foo`` in current working directory.
- Make any necessary adjustments so that you can run the project and start developing
  right away.
- The ``-e`` switch will make DevAssistant register the newly created projects into
  Eclipse (tries ``~/workspace`` by default, if you have any other, you need to specify
  it as an argument to ``-e``). This will also cause installation of Eclipse and PyDev,
  unless already installed.
- The ``-g`` switch will make DevAssistant register the project on Github and push
  sources there. DevAssistant will ask you for your Github password the first time
  you're doing this and then it will create Github API token and new SSH keys, so
  on any further invocation, this will be fully automatic. Note, that if your
  system username differs from your Github username, you must specify Github username
  as an argument to ``-g``.

.. _modifying_projects_cli:

Modifying Existing Projects
~~~~~~~~~~~~~~~~~~~~~~~~~~~

DevAssistant allows you to work with previously created projects. You can do
this by using ``da mod``, as opposed to ``da crt`` for creating::

   $ da mod eclipse

This will import previously created project into Eclipse (and possibly install
Eclipse and other dependencies implied by the project language). Optionally,
you can pass ``-p path/to/project`` if your current working directory is not
the project directory.

.. _preparing_environment_cli:

Preparing Environment
~~~~~~~~~~~~~~~~~~~~~

DevAssistant can set up environment and install dependencies for
executing aribtrary tasks or development of already existing project located
in a remote SCM (e.g. Github). For custom projects created
by DevAssistant, you can use the ``custom`` assistant::

   $ da prep custom -u scm_url

The plan is to also include assistants for well known and largely developed projects
(that, of course, don't contain ``.devassistant`` file). So in future you should be
able to do something like::

   $ da prep openstack

and it should do everything needed to get you started developing OpenStack in a way
that others do. But this is still somewhere in the future...

Custom Actions
~~~~~~~~~~~~~~
There are also some custom actions besides ``crt``, ``mod`` and ``prep``. For
the time being, these are not of high importance, but in future, these will
bring more functionality, such as making coffee for you.

``help``
  Displays help, what else?
``version``
  Displays current DevAssistant version.

Using GUI
---------

DevAssistant GUI provides the full functionality of
:ref:`Commandline Interface <cli_interface>` through a Gtk based application.

As opposed to CLI, which consists of three binaries, GUI provides all
assistant types (creating, modifying, preparing) in one, each type having
its own page.

The GUI workflow is dead simple:

- Choose the assistant that you want to use, click it and possibly choose
  a proper subassistant (e.g. ``django`` for ``python``).
- GUI displays a window where you can modify some settings and choose from
  various assistant-specific options.
- Click "Run" button and then just watch getting the stuff done. If your input
  is needed (such as confirming dependencies to install), DevAssistant will
  ask you, so don't go get your coffee just yet.
- After all is done, get your coffee and enjoy.

Currently Supported Assistants
------------------------------

*Please note that list of currently supported assistants may vary greatly in different
distributions, depending on available packages etc.*

Currently supported assistants with their specialties (if any):

Creating
~~~~~~~~

- C - a simple C project, allows you to create SRPM and build RPM by specifying ``-b``
- C++
- Java
  - JSF - Java Server Faces project
  - Maven - A simple Apache Maven project
- Perl
  - Class - Simple class in Perl
  - Dancer - Dancer framework project
- PHP
  - LAMP - Apache/MySQL/PHP project
- Python - all Python assistants allow you to use ``--venv`` switch, which will make
  DevAssistant create a project inside a Python virtualenv and install dependencies
  there, rather then installing them system-wide from RPM
  - Django - Initial Django project, set up to be runnable right away
  - Flask - A minimal Flask project with a simple view and script for managing the application
  - Library - A custom Python library
  - PyGTK - Sample PyGTK project
- Ruby
  - Rails - Initial Ruby on Rails project

Modifying
~~~~~~~~~

- Eclipse - add an existing project into Eclipse (doesn't work for some languages/frameworks)
- Vim - install some interesting Vim extensions and make some changes in ``.vimrc`` (these
  changes will not affect your default configuration, instead you have to use command
  ``let devassistant=1`` after invoking Vim)

Preparing
~~~~~~~~~

- Custom - checkout a custom previously created project from SCM (git only so far) and
  install needed dependencies
