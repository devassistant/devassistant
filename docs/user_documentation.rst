.. _our issue tracker on Github: https://github.com/bkabrda/devassistant/issues

User Documentation
==================

For a brief intro, please see :ref:`overview`. If something seems to be missing
or unclear either in this documentation or manpages, please let us know.
Bugs can be reported at `our issue tracker on Github`_.

Creating New Projects
---------------------

Developer Assistant can help you create your projects with one line in terminal.
For example::

   $ devassistant python django -n foo -e -g

This line will do the following:

- Install Django (RPM packaged) and all needed dependencies.
- Create a Django project named ``foo`` in current working directory.
- Make any necessary adjustments so that you can run the project and start developing
  right away.
- The ``-e`` switch will make devassistant register the newly created projects into
  Eclipse (tries ``~/workspace`` by default, if you have any other, you need to specify
  it as an argument to ``-e``). This will also cause installation of Eclipse and PyDev,
  unless already installed.
- The ``-g`` switch will make devassistant register the project on Github and push
  sources there. Devassistant will ask you for your Github password the first time
  you're doing this and then it will create Github API token and new SSH keys, so
  on any further invocation, this will be fully automatic. Note, that if your
  system username differs from your Github username, you must specify Github username
  as an argument to ``-g``.

Modifying Existing Projects
---------------------------

Developer Assistant allows you to work with previously created projects. You can do
this by using ``devassistant-modify``::

   $ devassistant-modify eclipse

This will import previously created project into Eclipse (and possibly install
Eclipse and other dependencies implied by the project language). Optionally,
you can pass ``-p path/to/project`` if your current working directory is not
the project directory.

Preparing Development Environment for Existing Projects
-------------------------------------------------------

Developer Assistant can set up environment and install dependencies for already
existing project located in a remote SCM (e.g. Github). For custom projects created
by devassistant, you can use the ``custom`` assistant::

   $ devassistant-prepare custom -u scm_url -p directory_to_save_to

The plan is to also include assistants for well known and largely developed projects
(that, of course, don't contain ``.devassistant`` file). So in future you should be
able to do something like::

   $ devassistant-prepare openstack

and it should do everything needed to get you started developing OpenStack in a way
that others do. But this is still somewhere in the future...


Currently Supported Assistants
------------------------------

*Please note that list of currently supported assistants may vary greatly in different
distributions, depending on available packages etc.*

Currently supported assistants with their specialties (if any):

Creating
^^^^^^^^

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
  devassistant create a project inside a Python virtualenv and install dependencies
  there, rather then installing them system-wide from RPM
  - Django - Initial Django project, set up to be runnable right away
  - Flask - A minimal Flask project with a simple view and script for managing the application
  - Library - A custom Python library
  - PyGTK - Sample PyGTK project
- Ruby
  - Rails - Initial Ruby on Rails project

Modifying
^^^^^^^^^

- Eclipse - add an existing project into Eclipse (doesn't work for some languages/frameworks)
- Vim - install some interesting Vim extensions and make some changes in ``.vimrc`` (these
  changes will not affect your default configuration, instead you have to use command
  ``let devassistant=1`` after invoking Vim)

Preparing
^^^^^^^^^

- Custom - checkout a custom previously created project from SCM (git only so far) and
  install needed dependencies
