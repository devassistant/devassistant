devassistant
============

Developer Assistant - start developing with ease.

The devassistant project is a helper for all developers using (not-only) Fedora. It help with creating and setting up basic projects in various languages, installing dependencies, setting up environment etc.

Devassistant is based on idea of per-{language/framework/...} "assistants" with hierarchical structure. E.g. you can run

.. code:: sh

  $ devassistant python django -n ~/myproject # sets up Django project named "myproject" inside your home dir
  $ devassistant python flask -n ~/flaskproject # sets up Flask project named "flaskproject" inside your home dir
  $ devassistant java jsf -n ~/alsomyproject # sets up RoR project named "alsomyproject" inside your home dir

This whole project is licensed under GPLv2+, see LICENSE file for details.
