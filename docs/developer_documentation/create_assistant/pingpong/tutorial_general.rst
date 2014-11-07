.. _tutorial_general_pingpong:

Tutorial: Assistants Utilizing PingPong
=======================================

Regardless of which language you want to choose for implementing the PingPong script,
you should read this section. It provides general information about specifying metadata,
dependencies, arguments and file placement for the PingPong scripts.

DevAssistant distinguishes four different :ref:`assistant roles <assistant_roles_devel>` -
Creator, Tweak, Preparer, Extras. From the point of view of this tutorial, the roles
only differ in file placement and where they'll be presented to user on command line/in GUI.
Therefore we choose to create a simple Creator. We'll be implementing an assistant, that
creates a simple `reStructuredText <http://docutils.sourceforge.net/rst.html>`_ document.

.. include:: ../terminology-note.txt

.. include:: ../common-rules.txt

Getting Set Up
--------------

To get started, we'll create a file hierarchy for our new assistant, say in
``~/programming``. We'll also modify ``DEVASSISTANT_PATH`` so that DevAssistant
can see this assistant in directory outside of standard load paths. Luckily,
there is assistant that does all this - `dap <https://dapi.devassistant.org/dap/dap/>`_::

   da pkg install dap
   da create dap -n ~/programming/rstcreate --crt
   export DEVASSISTANT_PATH=~/programming/rstcreate/

Running ``da create dap`` scaffolds everything that's needed to create a DAP package
that can be distributed on `DevAssistant Package Index, DAPI <https://dapi.devassistant.org/>`_,
see :ref:`packaging_and_distributing` for more information.

Since this assistant is a Creator, we need to put it somewhere under ``assistants/crt``
directory. The related files (if any), including the PingPong script have to go under
``files/crt/rstcreate`` (assuming, of course, we name the assistant ``rstcreate.yaml``).
More details on assistants file locations and subassistants can be found in the
:ref:`tutorial for the Yaml DSL <creating_yaml_creator>`.

Now go to one of the language-specific tutorials to see how to actually create a
simple assistant and the PingPong script.
