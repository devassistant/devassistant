python-daploader
================

Python module that loads a dap file, check it for sanity/validity
and provide access for metadata via a Python class.

dap
---

Dap is a format of extension for DevAssistant that contains custom assistants.
The whole thing is now in development phase and the specification may change
in the future. This module should define the standard.

http://devassistant.org

Structure
~~~~~~~~~

* <package_name>-<version>/

  * assistants/

    * {crt,mod,prep,task}/

      * <package_name>.yaml and optionally <package_name>/*.yaml

  * icons/

    * <package_name>.{svg,png...}

  * snippets/

    * <package_name>.yaml and optionally <package_name>/*.yaml

  * doc/

    * <package_name>/

      * LICENSE or COPYING file
      * README
      * other documentation

  * meta.yaml

    * metadata

Basically only meta.yaml is mandatory, but a dap with meta.yaml only makes no sense. All content is wrapped in tar.gz archive and renamed to <package_name>-<version>.dap. The archive should contain one top level directory named <package_name>-<version>.

meta.yaml
~~~~~~~~~

::

    package_name: foo # required
    version: 1.0.0 # required
    license: GPLv2 # required
    authors: [Bohuslav Kabrda <bkabrda@mailserver.com>, ...] # required
    homepage: https://github.com/bkabrda/assistant-foo # optional
    summary: Some brief one line text # required
    bugreports: <a single URL or email address> # optional
    description: |
        Some not-so-brief optional text.
        It can be split to multiple lines.

* **package name** can contain lowercase letters (ASCII only), numbers, underscore and dash (while it can only start and end with a letter or digit), it has to be unique, several names are reserved by DevAssitant itself (e.g. python, ruby)

* **version** follows this scheme: <num>[.<num>]*[dev|a|b], where 1.0.5 < 1.1dev < 1.1a < 1.1b < 1.1

* **license** is specified via license tag used in Fedora https://fedoraproject.org/wiki/Licensing:Main?rd=Licensing#Good_Licenses

* **authors** is a list of authors with their e-mail addresses (_at_ can be used instead of @)

* **homepage** is an URL to existing webpage that describes the dap or contains the code (such as in example), only http(s) or ftp is allowed, no IP addresses

* **summary** and **description** are self-descriptive in the given example

* **bugreports** defines where the user should report bugs, it can be either an URL (issue tracker) or an e-mail address (mailing list or personal)
