.. _create_pingpong_assistant:

Create Assistant Using DevAssistant PingPong
============================================

.. toctree::
   :titlesonly:

   pingpong/how_it_works_reference
   pingpong/tutorial_python

(:ref:`Why PingPong? <why_pingpong>`)

The PingPong approach is the second approach you can take to write assistants. It utilizes
a small subset of the :ref:`Yaml DSL <create_yaml_assistant>` for describing metadata,
dependencies and assistant arguments.

The actual execution part is written in one of the scripting languages listed above. For each
of these languages, there is a binding library available, that allows the PingPong script to
make callbacks to DevAssistant. Hence you can write assistants in a scripting language while
still utilizing DevAssistant functionality.
