Developer Documentation
=======================

.. toctree::
   :maxdepth: 2

   developer_documentation/yaml_assistant_reference
   developer_documentation/common_assistant_behaviour
   developer_documentation/devassistant_core

Overall Design
--------------

Developer Assistant consists of several parts:

Core
  Core of Developer Assistant is written in Python. It is responsible for
  interpreting Yaml Assistants and it provides an API that can be used
  by any consumer for the interpretation.
CL Interface
  CL interface allows users to interact with Developer Assistant
  on commandline; it consumes the Core API.
GUI
  (work in progress) GUI allows users to interact with Developer
  Assistant from GTK based GUI; it consumes the Core API.
Assistants
  Assistants are Yaml files with special syntax and semantics (defined
  in :ref:`yaml_assistant_reference`). They are indepent of the Core,
  therefore any software distribution can carry its own assistants
  and drop them into the directory from where Developer Assistant
  loads them - they will be loaded on next invocation.

Assistants
----------
Internally, each assistant is represented by a class (subclass of
devassistant.assistant_base.AssistantBase). This class is constructed
by devassistant in runtime from parsed yaml files. Each assistant can
have zero or more subassistants. This effectively forms a tree-like
structure. For example::

              MainAssistant
              /           \
             /             \
           Python          Ruby
           /   \            / \
          /     \          /   \
       Django  Flask    Rails Sinatra

Each assistant can optionally define arguments that it accepts (either
on commandline, or from GUI in future). For example, you can run
the leftmost path with::

   $ devassistant python [python assistant arguments] django [django assistant arguments]

If an assistant has any subassistants, one of them **must** be used. E.g.
in the example above, you can't use just Python assistant, you have to
choose between Django and Flask. If Django would get a subassistant, it
wouldn't be usable on its own any more, etc.


Contributing
------------

If you want to contribute (bug reporting, new assistants, patches for core,
improving documentation, ...),
please use our Github repo:

- code: https://github.com/bkabrda/devassistant
- issue tracker: https://github.com/bkabrda/devassistant/issues
