Tutorial: Python PingPong Script
================================

This tutorial explains how to write a Python assistant using PingPong protocol.
You should start by setting up the general things explained in
:ref:`general tutorial <tutorial_general_pingpong>`.

Creating the Yaml Assistant
---------------------------

Since one of the points of PingPong is to avoid as much of the Yaml DSL as possible, this
will be very short (and self-explanatory, too!). This is what you should put in
``~/programming/rstcreate/assistants/crt/rstcreate.yaml``::

  fullname: RST Document
  description: Create a simple reStructuredText document.

  dependencies:
  - rpm: [python3, python3-dapp]

  args:
    title:
      flags: [-t, --title]
      help: Title of the reStructuredText document.
      required: True

  files:
    ppscript: &ppscript
      source: ppscript.py

  run:
  - pingpong: python3 *ppscript

This is pretty much all you'll need to write in the Yaml DSL everytime you'll be writing
assistants based on PingPong. A brief explanation follows (more detailed explanation of the
DSL can be found at :ref:`tutorial_dsl`):

- ``fullname`` and ``description`` are "nice" attributes to show to users.
- ``dependencies`` list packages that DevAssistant is supposed to install prior to invoking
  the PingPong script; you can add any dependencies that your PingPong script needs here
- ``args`` are a Yaml mapping of arguments that the assistant will accept from user (be it
  on commandline or in GUI).
- ``files`` is a Yaml mapping of files; each file must a have a unique name (``ppscript``),
  should be referenced to by Yaml anchor (``&ppscript``; shouldn't be different from
  ``ppscript`` because of `issue 74 <https://github.com/devassistant/devassistant/issues/74>`_)
  and has to have ``source`` argument that specifies filename. (Will be searched for in
  appropriate ``files`` subdirectory.
- ``run`` just runs the PingPong script the way it's supposed to be run
  (the ``python3 *ppscript``) is exactly what will get executed to execute the PingPong
  subprocess (of course after substituting ``*ppscript`` with expanded path to the actual
  script from ``files``).

Creating the PingPong Script
----------------------------

We'll write the PingPong script in Python 3, using the
`dapp library <https://github.com/devassistant/dapp>`_. Note, that this tutorial uses
version 0.3.0 of dapp; consult dapp documentation if your version is different (you can
find a detailed documentation of this library at its
`Github project page <https://github.com/devassistant/dapp>`_).

This is the content of the ``~/programming/rstcreate/files/crt/rstcreate/ppscript.py``
file (see comments below for explanation)::

   #!/usr/bin/python3
   import os

   import dapp

   class MyScript(dapp.DAPPClient):
       def run(self, ctxt):
           # call a DA command that replaces funny characters by underscores,
           #  so that we can use title as a filename
           _, normalized = self.call_command(ctxt, 'normalize', ctxt['title'])
           filename = normalized.lower() + '.rst'

           # if file already exists, just fail
           if os.path.exists(filename):
               self.send_msg_failed(ctxt,
                   'File "{0}" already exists, cannot continue!'.format(filename))

           self.call_command(ctxt, 'log_i', 'Creating file {0} ...'.format(filename))
           with open(filename, 'w') as f:
               # Issue a debug message that will show if DA is run with --debug
               self.call_command(ctxt, 'log_d', 'Writing to file {0}'.format(filename))
               f.write(ctxt['title'].capitalize())
               f.write('\n')
               f.write('=' * len(ctxt['title']))

           # inform user that everything went fine and return
           self.call_command(ctxt, 'log_i', 'File {0} was created.'.format(filename))
           return (True, filename)

   if __name__ == '__main__':
       MyScript().pingpong()

- The PingPong script mustn't write anything to ``stdout`` or ``stderr``. If you need to
  tell something to user, use ``log_i`` command (``log_w`` for warnings and ``log_d`` for
  debug output).
- The whole PingPong script is just a Python 3 script that imports ``dapp`` library, subclasses
  the ``dapp.DAPPClient`` class and runs ``pingpong()`` method when script is run (*note: the
  implemented class has to implement run() method, but pingpong() has to be called!*).
- The ``run`` method takes ``ctxt`` as an argument, which is the Yaml DSL context. In short,
  it is a dictionary mapping DSL variables to their values. This context has to be passed
  as the first argument to all functions that interact with DevAssistant. Note, that all
  changes that you do to ``ctxt`` are permanent and will reflect in any subsequent Yaml DSL
  commands following the PingPong script invocation. See :ref:`variables_ctxt_ref` for more
  details on how context and variables work.
- You can run :ref:`DevAssistant commands <command_ref>` by calling ``self.call_command``
  method. It takes three parameters: Yaml DSL context, *command type* and *command input*
  (consult `command_ref` for details on command types and their input). This function
  returns 2-tuple, *logical result* (boolean) and *result* (type depends on command)
  (again, consult `command_ref`).
- You can pass arbitrary dictionaries (== crafted to make commands see a different context)
  to ``call_command()`` to achieve desired results. Doing this does *not* alter the Yaml DSL
  context in any way, the changes will be limited to the dictionary you pass.
- Similarly, the called commands can change the context that you pass to them as argument
  (usually they don't do this; if they do, they usually just add variables, not remove/change).
- The ``run()`` method has to return a 2-tuple, a *logical result* and *result*. This is exactly
  the same as what any DevAssistant command returns (since ``pingpong`` is in fact just a Yaml
  command). You can choose what you want to return as *result* as you wish - in this case, we
  return the name of the file created.

Wrap-up
-------

That is it. Now you can run the assistant with::

   da create rstcreate -t "My Article"

And that's it. Enjoy!
