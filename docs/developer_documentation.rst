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
