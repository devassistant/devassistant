Project Metainfo: the .devassistant File
========================================

**Note: .devassistant file changed some of its contents and semantics in version 0.9.0.**

Project created by DevAssistant usually get a ``.devassistant`` file, see
:ref:`dda_commands_ref` for information on creating and manipulating it by assistants.
This file contains information about a project, such as project type or paramaters
used when this project was created. It can look like this::

   devassistant_version: 0.9.0
   original_kwargs:
     name: foo
     github: bkabrda
   project_type: [python, django]
   dependencies:
   - rpm: [python-django]

When .devassistant is used
--------------------------

Generally, there are two use cases for ``.devassistant``:

- Modifier assistants read the ``.devassistant`` file to get project type
  (which is specified by ``project_type`` entry) and decide what to
  do with this type of project (by choosing a proper ``run`` section to
  execute and proper ``dependencies`` section, see :ref:`modifier_assistants_ref`).
- When you use the ``custom`` preparer with URL to this project
  (``da prepare custom -u <url>``), DevAssistant will checkout the project,
  read the data from ``.devassistant`` and do few things:

  - It will install any dependendencies that it finds in ``.devassistant``. These
    dependencies look like normal :ref:`dependencies section <dependencies_ref>` in
    assistant, e.g.::

     dependencies:
     - rpm: [python-spam]

  - It will also run a ``run`` section from ``.devassistant``, if it is there.
    Again, this is a normal :ref:`run section <run_sections_ref>`::

     run:
     - log_i: Hey, I'm running from .devassistant after checkout!

  Generally, when using ``custom`` assistant, you have to be **extra careful**,
  since someone could put ``rm -rf ~`` or similar evil command in the ``run``
  section. So use it **only with projects whose upstream you trust**.
