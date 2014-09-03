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

Another path(s) can be added by specifying ``DEVASSISTANT_PATH`` environment
variable (if more paths are used, they must be separated by colon). These paths
are prepended to the list of standard load paths.

Each load path entry has this structure::

   assistants/
     crt/
     mod/
     prep/
     task/
   files/
     crt/
     mod/
     prep/
     task/
     snippets/
   icons/
     crt/
     mod/
     prep/
     task/
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
the same applies to Modifier (``mod``), Preparer (``prep``) and Task (``task``) assistants.

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

.. _command_runners:

Command Runners
---------------
Command runners... well, they run commands. They are the functionality that 
makes DevAssistant powerful, since they effectively allow you to create
callbacks to Python, where you can cope with the hard parts unsuitable for
Yaml assistants.

When DevAssistant executes a ``run`` section, it reads commands one by one
and dispatches them to their respective command runners. Every command runner
can do whatever it wants - for example, we have a command runner that creates
Github repos.

After a command runner is run, DevAssistant sets ``LAST_LRES`` and ``LAST_RES`` global variables
for usage (these are rewritten with every command run). These variables represent the logical
result of the command (``True``/``False``) and result (a "return value", something computed),
much like with :ref:`expressions_ref`.

For reference of current commands, see :ref:`command_ref`.

If you're missing some cool functionality, you can implement your own command
runner and send us a pull request. (We're thinking of creating some sort of
import hook that would allow assistants to import command runners from Python
files outside of DevAssistant, but it's not on the priority list right now.)
Each command must be a class with two classmethods::

   @register_command_runner
   class MyCommandRunner(CommandRunner):
       @classmethod
       def matches(cls, c):
           return c.comm_type == 'mycomm'

       @classmethod
       def run(cls, c):
           input = c.input_res
           logger.info('MyCommandRunner was invoked: {ct}: {ci}'.format(ct=c.comm_type,
                                                                        ci=input))
           return (True, len(input))

This command runner will run all commands with command type ``mycomm``.
For example if your assistant contains::

   run:
   - $foo: $(echo "using DevAssistant")
   - mycomm: You are $foo!

than DevAssistant will print out something like::

   INFO: MyCommandRunner was invoked: mycomm: You are using DevAssistant!

When run, this command returns a tuple with *logical result* and *result*. This means
you can assign the length of a string to a variable like this::

   run:
   $thiswillbetrue, $length~:
   - mycomm: Some string.

(Also, ``LAST_LRES`` will be set to ``True`` and ``LAST_RES`` to length of the input string.)

Generally, the ``matches`` method should just decide (True/False) whether given
command is runnable or not and the ``run`` method should actually run it.
The ``run`` method should use ``devassistant.logger.logger`` object to log any
messages and it can also raise any exception that's subclass of
``devassistant.exceptions.ExecutionException``.

The ``c`` argument of both methods is a ``devassistant.lang.Command``
object. You can use various attributes of ``Command``:

- **comm_type** - command type, e.g. ``mycomm``
  (this will always be stripped of exec flag ``~``).
- **comm** - raw command input. The input is raw in the sense that it is uninterpreted.
  It's literally the same as what's written in assistant yaml file.
- **had_exec_flag** - ``True`` if the command type had exec flag, ``False`` otherwise.
- **input_log_res** and **input_res** - return values of input, see :ref:`section_results_ref`.

*Note: input only gets evaluated one time - at time of using input_log_res or input_res. This
means, among other things, that if exec flag is used, the command runner still has to access
input_log_res or input_res to actually execute the input.*
