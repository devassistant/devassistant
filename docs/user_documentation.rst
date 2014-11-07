.. _our issue tracker on Github: https://github.com/devassistant/devassistant/issues

User Documentation
==================

A Brief Intro
-------------

.. include:: brief-intro.txt

.. _cli_interface:

So What is an Assistant?
------------------------

In short, assistant is a recipe for creating/tweaking a project or setting up
the environment in a certain way. DevAssistant is in fact just a core that "runs"
assistants according to certain rules.

Each assistant specifies a way to achieve a single task, e.g. create a new
project in framework X of language Y.

If you want to know more about how this all works, consult
:ref:`create_your_own_assistant`.

Assistant Roles
~~~~~~~~~~~~~~~

.. include:: assistant-roles.txt

You can learn about how to invoke the
respective roles below in :ref:`creating_projects_cli`,
:ref:`tweaking_projects_cli`, :ref:`preparing_environment_cli` and
:ref:`extras_cli`.

Using Commandline Interface
---------------------------

.. _creating_projects_cli:

Creating New Projects
~~~~~~~~~~~~~~~~~~~~~

DevAssistant can help you create your projects with one line in a terminal. For example::

   $ da create python django -n foo -e -g

``da`` is the short form of ``devassistant``. You can use either of them, but ``da`` is preferred.

What this line does precisely depends on the author of the assistant. You can always
display help by using ``da create python django -h``. Running the above command line
*may* do something like this:

- Install Django and all needed dependencies.
- Create a Django project named ``foo`` in the current working directory.
- Make any necessary adjustments so that you can run the project and start developing
  right away.
- The ``-e`` switch will make DevAssistant register the newly created projects into
  Eclipse. This will also cause installation of Eclipse and PyDev,
  unless already installed.
- The ``-g`` switch will make DevAssistant register the project on Github and push
  sources there.

.. _tweaking_projects_cli:

Working with Existing Projects
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

DevAssistant allows you to work with previously created projects. You can do
this by using ``da tweak``, as opposed to ``da create`` for creating::

   $ da tweak eclipse

As noted above, what an assistant does depends on its author. In this case,
it seems that the assistant will import an existing project into Eclipse,
possibly installing missing dependencies - to find out if this assumption
is correct, run ``da tweak eclipse -h`` and read the help.

.. _preparing_environment_cli:

Preparing Environment
~~~~~~~~~~~~~~~~~~~~~

DevAssistant can set up the environment and install dependencies for
development of an already existing project located
in a remote SCM (e.g. Github). There is, for example, the so-called
`custom <https://dapi.devassistant.org/dap/custom/>`_ prepare
assistant, that is supposed to prepare environment for arbitrary upstream projects.
This means that it will checkout the source code from given git repo and if there
is a ``.devassistant`` file in the repo, it'll install dependencies and prepare
environment according to it::

   $ da prepare custom -u scm_url

**Warning:** The ``custom`` assistant executes custom pieces of code from a ``.devassistant`` file,
so use this only for projects whose upstreams you trust.

We hope that existance of DAPI will attract people from various upstreams to
create prepare assistants for their specific projects, so that people could do
something like::

   $ da prepare openstack

To get development environment prepared for development of OpenStack, etc...

.. _extras_cli:

Extras
~~~~~~

The last piece of functionality is performing arbitrary tasks that are not related to a specific
projects. E.g.::

   $ da extras make-coffee

Custom Actions
~~~~~~~~~~~~~~
There are also some custom actions besides ``create``, ``tweak``, ``prepare`` and ``extras``.
TODO: document ``pkg`` action.

- ``doc`` - Displays documentation for given DAP. Uses ``less`` as pager, if available.::

   # finds out if "python" DAP has documentation, lists documents if yes
   $ da doc python
   ...
   INFO: LICENSE
   INFO: somedoc.txt
   INFO: docsubdir/someotherdoc.txt
   ...

   # displays specific document for "python" DAP
   $ da doc python docsubdir/someotherdoc.txt

- ``help``- Displays help :)
- ``version``- Displays current DevAssistant version.

Using the GUI
-------------

The DevAssistant GUI provides the full functionality of
:ref:`Commandline Interface <cli_interface>` through a Gtk based application.

The GUI provides all assistant of the same type (creating, tweaking, preparing and extras)
in one tab to keep things organized.

The GUI workflow is dead simple:

- Choose the assistant that you want to use, click it and possibly choose
  a proper subassistant (e.g. ``django`` for ``python``).
- The GUI displays a window where you can modify some settings and choose from
  various assistant-specific options.
- Click the "Run" button and then just watch getting the stuff done. If your input
  is needed (such as confirming dependencies to install), DevAssistant will
  ask you, so don't go get your coffee just yet.
- After all is done, get your coffee and enjoy.
