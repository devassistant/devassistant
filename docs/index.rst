.. Developer Assistant documentation master file, created by
   sphinx-quickstart on Wed Jul 10 09:33:41 2013.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Developer Assistant's documentation!
===============================================

Developer Assistant - start developing with ease.

Contents
--------

.. toctree::
   :maxdepth: 2

   user_documentation
   developer_documentation

.. _overview:

Overview
--------

The devassistant project is a helper for all developers using (not-only) Fedora. It helps with creating and setting up basic projects in various languages, installing dependencies, setting up environment etc.

Devassistant is based on idea of per-{language/framework/...} "assistants" with hierarchical structure. E.g. you can run::

   $ devassistant python django -n ~/myproject # sets up Django project named "myproject" inside your home dir
   $ devassistant python flask -n ~/flaskproject # sets up Flask project named "flaskproject" inside your home dir
   $ devassistant java jsf -n ~/alsomyproject # sets up RoR project named "alsomyproject" inside your home dir

Devassistant also allows you to work with a previously created project, for example import it to Eclipse::

   $ devassistant-modify eclipse # run in project dir or use -p to specify path

Last but not least, devassistant allows you to check out a project from SCM (either previously created by devassistant with "custom" assistant or a specific project, assuming that you have the individual assistant for it)::

   $ devassistant-prepare custom ./devassistant-prepare.py custom -u scm_url -p directory_to_save_to

Devassistant works on Python 2.6, 2.7 and >= 3.3.

This whole project is licensed under GPLv2+.
