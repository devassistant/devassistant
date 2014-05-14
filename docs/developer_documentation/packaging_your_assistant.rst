Packaging Your Assistant
========================

**Note: this functionality is under heavy development and is not fully implemented yet.**

So now you know how to :ref:`create an assistant <tutorial>`.
But what if you want to share your assistant with others?

For that you could send them all the files from your assistant and tell them where they belong.
But that would be very unpleasant and that's why we've invented dap.
Dap is a format of extension for DevAssistant that contains custom assistants.
It means DevAssistant Package.

A dap is a tar.gz archive with ``.dap`` extension. The name of a dap is always
``<package_name>-<version>.dap`` - i.e. ``foo-0.0.1.dap``.

Directory structure of a dap
----------------------------

The directory structure of a dap copies the structure of ``~/.devassistant`` or
``/usr/share/devassistant`` folder. The only difference is, that it can only contain assistants,
files and icons that that belongs to it's namespace.

Each dap has an unique name (lat's say ``foo``) and it can only contain assistants ``foo`` or
``foo/*``. Therefore, the directory structure looks like this::

   foo-0.0.1/
     meta.yaml
     assistants/
       {crt,mod,prep,task}/
         foo.yaml
         foo/
     files/
       {crt,mod,prep,task,snippets}/
         foo/
     snippets/
       foo/
     icons/
       {crt,mod,prep,task,snippets}/
         foo.{png,svg}
         foo/
     doc/
         foo/

Note several things:

- Each of this is optional, i.e. you don't create ``files`` or ``snippets`` folder if you provide
  no files or snippets. Only mandatory thing is ``meta.yaml`` (see below).
- Everything goes to the particular folder, just like you've learn in the
  :ref:`Tutorial <tutorial>`. However, you can only add stuff named as your
  dap (means either a folder or a file with a particular extension). If you have more levels of
  assistants, such as ``crt/foo/bar/spam.yaml``, you have to include top-level assistants (in this
  case both ``crt/foo.yaml`` and ``crt/foo/bar.yaml``). And you have to preserve the structure
  in other folders as well (i.e. no ``icons/crt/foo/spam.svg`` but ``icons/crt/foo/bar/spam.svg``).
- The top level folder is named ``<package_name>-<version>``.

meta.yaml
---------

::

    package_name: foo # required
    version: 0.0.1 # required
    license: GPLv2 # required
    authors: [Bohuslav Kabrda <bkabrda@mailserver.com>, ...] # required
    homepage: https://github.com/bkabrda/assistant-foo # optional
    summary: Some brief one line text # required
    bugreports: <a single URL or email address> # optional
    description: |
        Some not-so-brief optional text.
        It can be split to multiple lines.
        
        BTW you can use **Markdown**.

* **package name** can contain lowercase letters (ASCII only), numbers, underscore and dash (while it can only start and end with a letter or digit), it has to be unique, several names are reserved by DevAssitant itself (e.g. python, ruby)

* **version** follows this scheme: <num>[.<num>]*[dev|a|b], where 1.0.5 < 1.1dev < 1.1a < 1.1b < 1.1

* **license** is specified via license tag used in Fedora https://fedoraproject.org/wiki/Licensing:Main?rd=Licensing#Good_Licenses

* **authors** is a list of authors with their e-mail addresses (_at_ can be used instead of @)

* **homepage** is an URL to existing webpage that describes the dap or contains the code (such as in example), only http(s) or ftp is allowed, no IP addresses

* **summary** and **description** are self-descriptive in the given example

* **bugreports** defines where the user should report bugs, it can be either an URL (issue tracker) or an e-mail address (mailing list or personal)

Checking your dap for sanity
----------------------------

Once you have your dap packaged, check it for sanity with ``daplint`` tool from ``daploader``.

First, you have to get the ``daplint`` tool.
Install `daploader <https://pypi.python.org/pypi/daploader/>`_ with ``pip`` or ``easy_install``.

::

   pip install daploader

Then you can check your dap with ``daplint``:

::

   daplint foo-0.0.1.dap

Uploading your dap to DevAssistant Package Index
------------------------------------------------

When you are satisfied, you can share your assistant on `Dapi <http://dapi.devassistant.org/>`_ (DevAssistant Package Index).

On `Dapi <http://dapi.devassistant.org/>`_, log in with Github or Fedora account and follow `Upload a Dap <http://dapi.devassistant.org/upload>`_ link in the menu.
