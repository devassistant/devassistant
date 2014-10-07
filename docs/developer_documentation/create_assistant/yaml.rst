.. _create_yaml_assistant:

Create Assistant in Yaml DSL
============================

.. toctree::
   :titlesonly:

   yaml/tutorial
   yaml/dsl_reference
   yaml/run_sections_reference
   yaml/snippets

Using DevAssistant Yaml DSL is the first option to create assistants.
The DSL is fairly simple and understandable and is very good at what it does. However,
it's not well suited for very complex computations (which you usually don't need to do
during project setup).

If, for some reason, you need to execute complex algorithms in assistants (or you just
don't want to learn the DSL), you can consider using the
:ref:`PingPong approach <create_pingpong_assistant>`, which basically
lets you write assistants in popular scripting languages.
