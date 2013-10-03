DevAssistant Core
=================

*Note: So far, this only covers some bits and pieces of the whole core.*

.. _load_paths:

DevAssistant Load Paths
-----------------------
DevAssistant has couple of load path entries, that are searched for assistants,
snippets, icons and files used by assistants. In standard installations,
there are three paths:

1. "system" path, which is defined by OS distribution (usually
   ``/usr/share/devassistant/``) or by Python installation
   (sth. like ``/usr/share/pythonX.Y/devassistant/data/``)
2. "local" path, ``/usr/local/share/devassistant/``
3. "user" path, ``~/.devassistant/``

Each load path entry has this structure::

   assistants/
     crt/
     mod/
     prep/
   files/
     crt/
     mod/
     prep/
     snippets/
   icons/
     crt/
     mod/
     prep/
   snippets/

Icons under ``icons`` directory and files in ``files`` directory "copy"
must the structure of ``assistants`` directory. E.g. for assistant
``assistants/crt/foo/bar.yaml``, the icon must be ``icons/crt/foo/bar.svg``
and files must be placed under ``files/crt/foo/bar/``

.. _assistants_loading_mechanism:

Assistants Loading Mechanism
----------------------------
DevAssistant loads assistants from all load paths mentioned above (more
specifically from ``<load_path>/assistants/`` only), traversing them in
order "system", "local", "user".

When DevAssistant starts up, it loads all assistants from all these paths. It
assumes, that Creator assistants are located under ``crt`` subdirectories
the same applies to Modifier (``mod``) and Preparer (``prep``) assistants.

For example, loading process for Creator assistants looks like this:

1. Load all assistants located in ``crt`` subdirectories of each
   ``<load path>/assistants/`` (do not descend into subdirectories).
   If there are multiple assistants with the same name in different
   load paths, the first traversed wins.
2. For each assistant named ``foo.yaml``:

   a. If ``crt/foo`` directory doesn't exist in any load path entry, then this
      assistant is "leaf" and therefore can be directly used by users.
   b. Else this assistant is not leaf and DevAssistant loads its subassistants
      from the directory, recursively going from point 1).

