Project Metainfo: the .devassistant File
========================================

Each project created by DevAssistant gets a ``.devassistant`` file. This
file contains information about the project, such as used Creator assistant or
given paramaters. It can look like this::

   devassistant_version: 0.7.0
   original_kwargs:
     name: foo
     github: bkabrda
   subassistant_path:
   - python
   - django

When .devassistant is used
--------------------------

Generally, there are two use cases for ``.devassistant``:

- Modifier assistants read the ``.devassistant`` file to get project type
  (which is specified by ``subassistant_path`` entry) and decide what to
  do with this type of project (by choosing a proper ``run`` section to
  execute, see :ref:`modifier_assistants_ref`).
- When you use the ``custom`` preparer with URL to this project
  (``da prep custom -u <url>``), DevAssistant will checkout the project,
  read the data from ``.devassistant`` and install dependencies according
  to specified ``subassistant_path``, assuming the local copy of DevAssistant
  knows given assistants (e.g. if your installation of DevAssistant doesn't
  have ``python`` or ``django`` assistant, DevAssistant will just print a
  warning, but won't install dependencies for those).

  Another nice thing about ``custom`` assistant is, that it will install any
  dependendencies that it finds in ``.devassistant``. These dependencies
  look like normal :ref:`dependencies section <dependencies_ref>` in assistant,
  e.g.::

   dependencies:
   - rpm: [python-spam]

  It will also run a ``run`` section from ``.devassistant``, if it is there.
  Again, this is a normal :ref:`run section <run_ref>`::

   run:
   - log_i: Hey, I'm running from .devassistant after checkout!

  Generally, when using ``custom`` assistant, you have to be **extra careful**,
  since someone could put ``rm -rf ~`` or similar evil command in the ``run``
  section. So use it **only with projects whose upstream you trust**.
