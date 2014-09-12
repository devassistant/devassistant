DevAssistant
============

.. image:: https://badge.fury.io/py/devassistant.png
    :target: http://badge.fury.io/py/devassistant

.. image:: https://travis-ci.org/devassistant/devassistant.png?branch=0.9.x
        :target: https://travis-ci.org/devassistant/devassistant

.. image:: https://pypip.in/d/devassistant/badge.png
        :target: https://pypi.python.org/pypi/devassistant

DevAssistant - making life easier for developers

DevAssistant (http://devassistant.org) project is a helper for all developers using (not-only) Fedora. It helps with creating and setting up basic projects in various languages, installing dependencies, setting up environment etc.

DevAssistant is based on idea of per-{language/framework/...} "assistants" with hierarchical structure. E.g. you can create projects like this:

.. code:: sh

  $ da create python django -n ~/myproject # sets up Django project named "myproject" inside your home dir
  $ da create python flask -n ~/flaskproject # sets up Flask project named "flaskproject" inside your home dir
  $ da create ruby rails -n ~/alsomyproject # sets up RoR project named "alsomyproject" inside your home dir

DevAssistant also allows you to work with a previously created project, for example import it to Eclipse:

.. code:: sh

  $ da modify eclipse # run in project dir or use -p to specify path

With DevAssistant, you can also prepare environment for developing upstream projects - either using project-specific assistants or using "custom" assistant for arbitrary projects (even those not created by DevAssistant):

.. code:: sh

  $ da prepare custom -u scm_url -p directory_to_save_to

Last but not least, DevAssistant allows you to perform arbitrary tasks not related to a specific project:

.. code:: sh

  $ da task <TODO:NOTHING YET>

For full documentation, see http://doc.devassistant.org/

Should you have some questions, feel free to ask us at Freenode channel #devassistant or on our mailing list (https://lists.fedoraproject.org/mailman/listinfo/devassistant). You can also join our G+ community (https://plus.google.com/u/0/communities/112692240128429771916) or follow us on Twitter (https://twitter.com/dev_assistant).

If you want to see where DevAssistant development is going and you want to influence it and send your suggestions and comments, you should *really* join our ML: https://lists.fedoraproject.org/mailman/listinfo/devassistant.

To start developing, do:

.. code:: sh

  git clone https://github.com/devassistant/devassistant
  cd devassistant
  git submodule init
  git submodule update

And install dependencies from requirements-devel.txt:

.. code:: sh

  pip install -r requirements-devel.txt

Apart from git, DevAssistant also assumes that polkit is installed on your machine (provides pkexec binary). If you want to work with GUI, you'll need pygobject3.

Or, assuming that you have DevAssistant version 0.8.0 or higher installed, you just need to do:

.. code:: sh

  da prepare devassistant

DevAssistant works on Python 2.6, 2.7 and >= 3.3.

This whole project is licensed under GPLv2+, see LICENSE file for details.
