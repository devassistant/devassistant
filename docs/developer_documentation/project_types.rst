.. _project_types_ref:

Project Types
=============

This is a list of official project types that projects should use in their
``.devassistant`` file and Creator assistants should state. If you choose one
of the official project types, there is a good chance that Modifier and Preparer
assistants written by others will work well with projects created by your Creator.

The project type is given as a list of strings - these describe the project from
the most general type to the most specific. E.g::

   project_type: [python, django]

If you don't use ``project_type`` in your Creator assistant, it will be automatically
supported to ``.devassistant``: If your assistant is ``crt/footest/foobar.yaml``, project
type in ``.devassistant`` will be ``[footest, foobar]``. This means that Modifier and
Preparer assistants written by others may not work well with your project, but otherwise
it does no harm.

Current List of Types
---------------------
Current project types list follows. If you want anything added in here,
open a bug for us at https://github.com/devassistant/devassistant/issues.
**Note: the list is currently not very thorough and it is meant to grow
as we get requested by assistant developers.**

- c
- cpp
- java
- nodejs

  - express

- perl

  - dancer

- php
- python

  - django
  - flask
  - gtk3
  - lib

- ruby

  - rails
