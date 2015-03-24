DevAssistant
============

.. image:: https://badge.fury.io/py/devassistant.png
    :target: http://badge.fury.io/py/devassistant

.. image:: https://travis-ci.org/devassistant/devassistant.png?branch=master
        :target: https://travis-ci.org/devassistant/devassistant

.. image:: https://pypip.in/d/devassistant/badge.png
        :target: https://pypi.python.org/pypi/devassistant

DevAssistant - start developing with ease

DevAssistant (http://devassistant.org) can help you with creating and setting up basic projects
in various languages, installing dependencies, setting up environment etc.

It is based on idea of per-{language/framework/...} "assistants" (plugins) with hierarchical
structure.

*Note: prior to version 0.10.0, DevAssistant has been shipped with a default set of assistants
that only worked on Fedora. We decided to drop this default set and create
DAPI, DevAssistant Package Index,* https://dapi.devassistant.org/ *- an upstream
PyPI/Rubygems-like repository of packaged assistants. DAPI's main aim is to create a community
around DevAssistant and provide various assistants with good support for various platforms -
a task that DevAssistant core team alone is not able to achieve for a large set of assistants.*

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

These are some examples of what you can do:

.. code:: sh

  # search for assistants that have "Django" in their description
  $ da pkg search django
  python - Python assistants (library, Django, Flask, GTK3)

  # install the found "python" DAP, assuming it supports your OS/distro (and, 
  # if you want to install sevaral assistants, just separate them by a space)
  $ da pkg install python

  # find out if the installed package has documentation
  $ da doc python
  INFO: DAP "python" has these docs:
  ...
  INFO: usage.txt
  ...
  # show help
  $ da doc python usage.txt

  # if the documentation doesn't say it specifically, find out if there is a "create"
  #  assistant in the installed "python" DAP
  $ da create -h
  ...
  {..., python, ...}
  ...

  # there is, so let's find out if it has any subassistants
  $ da create python -h
  ...
  {..., django, ...}
  ...

  # we found out that there is "django" subassistant, let's find out how to use it
  $ da create python django -h
  <help text with commandline options>

  # help text tells us that django assistant doesn't have subassistants and is runnable, let's do it
  $ da create python django -n ~/myproject # sets up Django project named "myproject" inside your home dir

  # using the same approach with "pkg search", "pkg install" and "da tweak -h",
  #  we find, install and read help for "tweak" assistant that imports projects to eclipse
  $ da tweak eclipse -p ~/myproject # run in project dir or use -p to specify path

  # using the same approach, we find, install and read help for assistant
  #  that tries to prepare environment for a custom upstream project, possibly utilizing
  #  its ".devassistant" file
  $ da prepare custom -u scm_url -p directory_to_save_to

  # sometimes, DevAssistant can really do a very special thing for you ...
  $ da extras make-coffee

For full documentation, see http://doc.devassistant.org/

Should you have some questions, feel free to ask us at Freenode channel #devassistant
or on our mailing list (https://lists.fedoraproject.org/mailman/listinfo/devassistant).
You can also join our G+ community (https://plus.google.com/u/0/communities/112692240128429771916)
or follow us on Twitter (https://twitter.com/dev_assistant).

If you want to see where DevAssistant development is going and you want to influence it and send
your suggestions and comments, you should *really* join our ML:
https://lists.fedoraproject.org/mailman/listinfo/devassistant.

To start developing, do:

.. code:: sh

  git clone https://github.com/devassistant/devassistant

And install dependencies from requirements-devel.txt:

.. code:: sh

  pip install --user -r requirements-devel.txt
  pip install --user -r requirements-py2.txt # Only on Python 2

Apart from git, DevAssistant also assumes that polkit is installed on your machine
(provides pkexec binary). If you want to work with GUI, you'll need pygobject3.

Or, assuming that you have "devassistant" DAP installed [TODO:link], you just need to do:

.. code:: sh

  da prepare devassistant

DevAssistant works on Python 2.6, 2.7 and >= 3.3.

This whole project is licensed under GPLv2+, see LICENSE file for details.

List of contributors to this project can be found in the CONTRIBUTORS file.
