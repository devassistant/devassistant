DevAssistant
============

.. image:: https://badge.fury.io/py/devassistant.png
    :target: http://badge.fury.io/py/devassistant

.. image:: https://travis-ci.org/bkabrda/devassistant.png?branch=master
        :target: https://travis-ci.org/bkabrda/devassistant

.. image:: https://pypip.in/d/devassistant/badge.png
        :target: https://pypi.python.org/pypi/devassistant

DevAssistant - making life easier for developers

DevAssistant project is a helper for all developers using (not-only) Fedora. It helps with creating and setting up basic projects in various languages, installing dependencies, setting up environment etc.

DevAssistant is based on idea of per-{language/framework/...} "assistants" with hierarchical structure. E.g. you can create projects like this:

.. code:: sh

  $ da crt python django -n ~/myproject # sets up Django project named "myproject" inside your home dir
  $ da crt python flask -n ~/flaskproject # sets up Flask project named "flaskproject" inside your home dir
  $ da crt ruby rails -n ~/alsomyproject # sets up RoR project named "alsomyproject" inside your home dir

DevAssistant also allows you to work with a previously created project, for example import it to Eclipse:

.. code:: sh

  $ da mod eclipse # run in project dir or use -p to specify path

Last but not least, DevAssistant allows you to prepare environment for executing arbitrary tasks or developing upstream projects (either using "custom" assistant for projects previously created by DevAssistant or using specific assistant for specific projects):

.. code:: sh

  $ da prep custom -u scm_url -p directory_to_save_to

For full documentation, see http://doc.devassistant.org/

To start developing, do:

.. code:: sh

  git clone https://github.com/bkabrda/devassistant
  cd devassistant
  git submodule init
  git submodule update

And install dependencies from requirements-devel.txt:

.. code:: sh

  pip install -r requirements-devel.txt

Apart from git, DevAssistant also assumes that polkit is installed on your machine (provides pkexec binary). If you want to work with GUI, you'll need pygobject3.

Or, assuming that you have DevAssistant version 0.8.0 or higher installed, you just need to do:

.. code:: sh

  da prep devassistant

DevAssistant works on Python 2.6, 2.7 and >= 3.3.

This whole project is licensed under GPLv2+, see LICENSE file for details.
