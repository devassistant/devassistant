Developer Documentation
=======================

.. toctree::
   :titlesonly:
   :maxdepth: 2

   developer_documentation/devassistant_core
   developer_documentation/tutorial_creating_assistant
   developer_documentation/yaml_assistant_reference
   developer_documentation/common_assistant_behaviour
   developer_documentation/dot_devassistant

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
  in :ref:`yaml_assistant_reference`). They are indepent of the Core,
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

   $ da crt python [python assistant arguments] django [django assistant arguments]

If an assistant has any subassistants, one of them **must** be used. E.g.
in the example above, you can't use just Python assistant, you have to
choose between Django and Flask. If Django would get a subassistant, it
wouldn't be usable on its own any more, etc.

.. _assistant_roles_devel:

Assistant Roles
~~~~~~~~~~~~~~~

The ``crt`` in the above example means, that we're running an assistant that
creates a project.

.. include:: assistant-roles.txt


Contributing
------------

If you want to contribute (bug reporting, new assistants, patches for core,
improving documentation, ...), please use our Github repo:

- code: https://github.com/bkabrda/devassistant
- issue tracker: https://github.com/bkabrda/devassistant/issues

Unless you actually have DevAssistant installed, you can checkout the sources
like this (just copy&paste this to get the job done)::

   git clone https://github.com/bkabrda/devassistant
   # get the official set of assistants
   cd devassistant
   git submodule init
   git submodule update

You can find list of core Python dependencies in file ``requirements.txt``.
On top of that, you'll need ``pygobject`` if you want to play around with GUI.
DevAssistant also assumes that ``git`` is installed on your system.

In next version, we will include a ``prep`` assistant, that will be able to
actually do this for you... Sweet, ain't it?
