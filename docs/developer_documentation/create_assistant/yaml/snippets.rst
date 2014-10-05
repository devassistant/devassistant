.. _snippets:

Snippets
========

Snippets are the DevAssistant's way of sharing common pieces of assistant code. For example,
if you have two assistants that need to log identical messages, you want the messages
to be in one place, so that you don't need to change them twice when a change is needed.

Example
-------

Let's assume we have two assistants like this::

   ### assistants/crt/assistant1.yaml
   ...
   run:
   - do: some stuff
   - log_i: Creating cool project $name ...
   - log_i: Still creating ...
   - log_i: I suggest you go have a coffee ...
   - do: more stuff

   ### assistants/crt/assistant2.yaml
   ...
   run:
   - do: some slightly different stuff
   - log_i: Creating cool project $name ...
   - log_i: Still creating ...
   - log_i: I suggest you go have a coffee ...
   - do: more slightly different stuff

So we have two assistants that have three lines of identical code in them - that breaks a widely
known programmer best practice: Don't do it twice, write a function for it.
In DevAssistant terms, we'll write a run section and place it in a snippet::

   ### snippets/mysnip.yaml
   run:
   - log_i: Creating cool project $name ...
   - log_i: Still creating ...
   - log_i: I suggest you go have a coffee ...

Then we'll change the two assistants like this (we'll utilize
:ref:`"use" command runner <use_commands_ref>`)::

   ### assistants/crt/assistant1.yaml
   ...
   run:
   - do: some stuff
   - use: mysnip.run
   - do: more stuff

   ### assistants/crt/assistant2.yaml
   ...
   run:
   - do: some slightly different stuff
   - use: mysnip.run
   - do: more slightly different stuff

How Snippets Work
-----------------

This section summarizes important notes about how snippets are formed and how they work.

Syntax and Sections
~~~~~~~~~~~~~~~~~~~

Snippets are very much like assistants. They can (but don't have to) have `args`,
`dependencies*` and `run*` sections - structured in the same manner as in assistants.
A snippet can contain any combination of the above sections (even empty file is a valid snippet).

Variables
~~~~~~~~~

When a snippet section is called (this applies to both `dependencies*` and `run*`, it gets
a copy of all arguments of its caller - e.g. it can use the variables, it can assign to them,
but they'll be unchanged in the calling section after the snippet finishes.

Using Snippets and Return Value
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

As noted above, snippets can hold 3 types of content (`args`, `dependencies*` sections
and `run*` sections), each of which can be used in assistants::

   ### snippets/mysnip.yaml

   args:
     foo:
       flags: [-f, --foo]
       help: Foo is foo
       required: True

   dependencies:
   - rpm: [python3]

   run:
   - log_i: Spam spam spam

   ### assistants/crt/assistant1.yaml

   args:
     foo:
       use: mysnip

   dependencies:
   - use: mysnip.dependencies

   run:
   - do: stuff
   - use: mysnip.run

Return values (RES and LRES) of snippet are determined by the
:ref:`use command runner <use_commands_ref>` - RES and LRES of last command of the snippet section.
