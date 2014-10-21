.. _create_pingpong_assistant:

Create Assistant Using Scripting Language (a.k.a DevAssistant PingPong)
=======================================================================

.. toctree::
   :titlesonly:

   pingpong/how_it_works_reference
   pingpong/tutorial_general
   pingpong/tutorial_python

(:ref:`Why PingPong? <why_pingpong>`)

The PingPong approach is the second approach you can take to write complex assistant
functionality. It utilizes a small subset of the :ref:`Yaml DSL <create_yaml_assistant>`
for describing metadata, dependencies and assistant arguments.

The actual execution part is written in one of the supported :ref:`pingpong_supported_languages`.
For each of these languages, there is a binding library available, that allows the PingPong
script to make callbacks to DevAssistant. Hence you can write assistants in a scripting
language while still utilizing DevAssistant functionality.

The general part about metadata, dependencies and arguments is described at
:ref:`tutorial_general_pingpong` and you should read it regardless of the language
you choose to implement the script. Then you should choose a language-specific tutorial
to see how to write the actual PingPong script.

.. _pingpong_supported_languages:

Supported Languages
-------------------

Currently, only Python PingPong client library has been implemented. It works with
Python 2.6, 2.7 and > 3.3. You can get it at `https://pypi.python.org/pypi/dapp`,
bug reports/feature requests are welcome at `https://github.com/devassistant/dapp/issues`.
This library is maintained by developers of DevAssistant.

.. include:: terminology-note.txt
