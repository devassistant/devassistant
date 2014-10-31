.. _common_assistant_behaviour:

Common Assistant Behaviour
--------------------------

Common Parameters of Assistants and Their Meanings
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

``-e``
  Create Eclipse project, optional. Should create ``.project`` (or any other 
  appropriate file) and register project to Eclipse workspace (``~/workspace``
  by default, or the given path if any).
``-g``
  Register project on GitHub (uses current user name by default, or given name if any).
``-n``
  Name of the project to create, mandatory. Should also be able to accept full or
  relative path.
``-p``
  Path to existing project supplied to tweak assistants (optional, defaults to ``.``).

To include these parameters in your assistant with common help strings etc., include
them from ``common_args.yaml`` (``-n``, ``-g``) or ``eclipse.yaml`` (``-e``) snippet::

   args:
     name:
       snippet: common_args

Other Conventions
^^^^^^^^^^^^^^^^^

When creating snippets/Python commands, they should operate under the assumption
that current working directory is the project directory (not one dir up or
anywhere else). It is the duty of assistant to switch to that directory. The benefit
of this approach is that you just ``cd`` once in assistant and then call all the
snippets/commands, otherwise you'd have to put 2x ``cd`` in every snippet/command.
