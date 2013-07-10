devassistant
============

Developer Assistant - start developing with ease.

Devassistant project is a helper for all developers using (not-only) Fedora. It helps with creating and setting up basic projects in various languages, installing dependencies, setting up environment etc.

Devassistant is based on idea of per-{language/framework/...} "assistants" with hierarchical structure. E.g. you can run:

.. code:: sh

  $ devassistant python django -n ~/myproject # sets up Django project named "myproject" inside your home dir
  $ devassistant python flask -n ~/flaskproject # sets up Flask project named "flaskproject" inside your home dir
  $ devassistant java jsf -n ~/alsomyproject # sets up RoR project named "alsomyproject" inside your home dir

Devassistant also allows you to work with a previously created project, for example import it to Eclipse:

.. code:: sh
  $ devassistant-modify eclipse # run in project dir or use -p to specify path

Last but not least, devassistant allows you to check out a project from SCM (either previously created by devassistant with "custom" assistant or a specific project, assuming that you have the individual assistant for it):

.. code:: sh
  $ devassistant-prepare custom -u scm_url -p directory_to_save_to

For full documentation, see https://developer-assistant.readthedocs.org/

Devassistant works on Python 2.6, 2.7 and >= 3.3.

This whole project is licensed under GPLv2+, see LICENSE file for details.
