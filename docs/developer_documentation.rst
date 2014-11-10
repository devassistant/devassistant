Developer Documentation
=======================

.. toctree::
   :titlesonly:

   developer_documentation/devassistant_core
   developer_documentation/create_assistant
   developer_documentation/command_reference
   developer_documentation/dot_devassistant
   developer_documentation/project_types
   developer_documentation/contributing

Talk to Us!
-----------

If you want to see where DevAssistant development is going and you want to influence it
and send your suggestions and comments, you should join our ML:
https://lists.fedoraproject.org/mailman/listinfo/devassistant. We also have IRC channel
#devassistant on Freenode and you can join our
`Google+ community <https://plus.google.com/communities/112692240128429771916>`_.

Overall Design
--------------

DevAssistant consists of several parts:

Core
  Core of DevAssistant is written in Python. It is responsible for
  interpreting Yaml Assistants and it provides an API that can be used
  by any consumer for the interpretation.
CL Interface
  CL interface allows users to interact with DevAssistant
  on commandline; it consumes the Core API.
GUI
  (work in progress) GUI allows users to interact with Developer
  Assistant from GTK based GUI; it consumes the Core API.
Assistants
  Assistants are Yaml files with special syntax and semantics (defined
  in :ref:`dsl_reference`). They are indepent of the Core,
  therefore any software distribution can carry its own assistants
  and drop them into the directory from where DevAssistant
  loads them - they will be loaded on next invocation.
  Note, that there is also a possibility to write assistants in Python,
  but this is no longer supported and will be removed in near future.

Assistants
----------
Internally, each assistant is represented by instance of
``devassistant.yaml_assistant.YamlAssistant``. Instances are constructed
by DevAssistant in runtime from parsed yaml files. Each assistant can
have zero or more subassistants. This effectively forms a tree-like
structure. For example::

              MainAssistant
              /           \
             /             \
           Python          Ruby
           /   \            / \
          /     \          /   \
       Django  Flask    Rails Sinatra

This structure is defined by filesystem hierarchy as explained in
:ref:`assistants_loading_mechanism`

Each assistant can optionally define arguments that it accepts (either
on commandline, or from GUI). For example, you can run
the leftmost path with::

   $ da create python [python assistant arguments] django [django assistant arguments]

If an assistant has any subassistants, one of them **must** be used. E.g.
in the example above, you can't use just Python assistant, you have to
choose between Django and Flask. If Django would get a subassistant, it
wouldn't be usable on its own any more, etc.

.. _assistant_roles_devel:

Assistant Roles
~~~~~~~~~~~~~~~

The ``create`` in the above example means, that we're running an assistant that
creates a project.

.. include:: assistant-roles.txt


Writing Assistants: Yaml or Scripting Languages
-----------------------------------------------

There are two ways to write assistants. You can either use our
:ref:`Yaml based DSL <create_yaml_assistant>` or
write assistants in popular scripting languages (for list of supported languages see
:ref:`pingpong_supported_languages`).
This method is referred to as :ref:`DevAssistant PingPong <create_pingpong_assistant>`.

Contributing
------------

If you want to contribute (bug reporting, new assistants, patches for core,
improving documentation, ...), please use our Github repo:

- code: https://github.com/devassistant/devassistant
- issue tracker: https://github.com/devassistant/devassistant/issues

If you have DevAssistant installed (version 0.8.0 or newer), there is a fair chance that you have
``devassistant`` preparer. Just run ``da prepare devassistant`` and it will
checkout our sources and do all the boring stuff that you'd have to do
without DevAssistant.

If you don't have DevAssistant installed, you can checkout the sources
like this (just copy&paste this to get the job done)::

   git clone https://github.com/devassistant/devassistant

You can find list of core Python dependencies in file ``requirements.txt``. If you want
to write and run tests (you should!), install dependencies from ``requirements-devel.txt``::

   pip install --user -r requirements-devel.txt

If you develop on Python 2, you'll also need to install extra dependencies::

   pip install --user -r requirements-py2.txt

Regardless of Python version, you'll need ``polkit`` for requesting root privileges for dependency installation
etc. If you want to play around with GUI, you have to install ``pygobject``, too.
To run guitest, you also need to install `behave <https://pypi.python.org/pypi/behave>`_ from PyPI and dogtail
(not on PyPI, get it from `Fedora Hosted <https://fedorahosted.org/dogtail/>`_ or from your favorite package manager).
(See how hard this is compared to ``da prepare devassistant``?)
