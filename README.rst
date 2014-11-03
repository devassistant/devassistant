DevAssistant
============

.. image:: https://badge.fury.io/py/devassistant.png
    :target: http://badge.fury.io/py/devassistant

.. image:: https://travis-ci.org/devassistant/devassistant.png?branch=master
        :target: https://travis-ci.org/devassistant/devassistant

.. image:: https://pypip.in/d/devassistant/badge.png
        :target: https://pypi.python.org/pypi/devassistant

DevAssistant - start developing with ease

DevAssistant (http://devassistant.org) project is a helper for all developers using (not-only)
Fedora. It helps with creating and setting up basic projects in various languages, installing
dependencies, setting up environment etc.

It is based on idea of per-{language/framework/...} "assistants" (plugins) with hierarchical
structure.

*Note: prior to version 0.10.0, DevAssistant has been shipped with a default set of assistants
that only worked on Fedora. We decided to drop this default set and create
DAPI, DevAssistant Package Index,* https://dapi.devassistant.org/ *- an upstream
PyPI/Rubygems-like repository of packagedassistants. DAPI's main aim is to create a community
around DevAssistant and provide various assistants for various platforms.*

*This all means that if you get DevAssistant from upstream repo or from PyPI, you will have
no assistants installed by default. To get assistants, search DAPI through web browser or run*
``da pkg search <term>`` *and* ``da pkg install <assistant package>`` *. This will install
one or more DAPs (DevAssistant Packages) with the desired assistants.*

If you want to create your own assistants and upload them to DAPI, see
http://docs.devassistant.org/en/latest/developer_documentation/create_assistant.html and
http://docs.devassistant.org/en/latest/developer_documentation/create_assistant/packaging_and_distributing.html.

There are four main modes of DevAssistant execution. Explanations are provided to better
illustrate what each mode is supposed to do:

``create``
  Create new projects - scaffold source code, install dependencies, initialize SCM repos ...
``tweak``
  Work with existing projects - add source files, import to IDEs, push to GitHub, ...
``prepare``
  Prepare environment for working with existing upstream projects - install dependencies,
  set up services, ...
``extras``
  Tasks not related to a specific project, e.g. enabling services, setting up IDEs, ...

These are some examples of what you can do assuming you have the right DAPs installed:

.. code:: sh

  # create a new Django project and import it to Eclipse
  $ da create python django -n ~/myproject # sets up Django project named "myproject" inside your home dir
  $ da tweak eclipse -p ~/myproject # run in project dir or use -p to specify path

  # Prepare environment for a custom upstream project, read the specific setup from its .devassistant file
  $ da prepare custom -u scm_url -p directory_to_save_to

  # Make a coffee
  $ da extras make-coffee

For full documentation, see http://doc.devassistant.org/

Should you have some questions, feel free to ask us at Freenode channel #devassistant or on our mailing list (https://lists.fedoraproject.org/mailman/listinfo/devassistant). You can also join our G+ community (https://plus.google.com/u/0/communities/112692240128429771916) or follow us on Twitter (https://twitter.com/dev_assistant).

If you want to see where DevAssistant development is going and you want to influence it and send your suggestions and comments, you should *really* join our ML: https://lists.fedoraproject.org/mailman/listinfo/devassistant.

To start developing, do:

.. code:: sh

  git clone https://github.com/devassistant/devassistant

And install dependencies from requirements-devel.txt:

.. code:: sh

  pip install --user -r requirements-devel.txt
  pip install --user -r requirements-py2.txt # Only on Python 2

Apart from git, DevAssistant also assumes that polkit is installed on your machine (provides pkexec binary). If you want to work with GUI, you'll need pygobject3.

Or, assuming that you have DevAssistant version 0.8.0 or higher installed, you just need to do:

.. code:: sh

  da prepare devassistant

DevAssistant works on Python 2.6, 2.7 and >= 3.3.

This whole project is licensed under GPLv2+, see LICENSE file for details.
