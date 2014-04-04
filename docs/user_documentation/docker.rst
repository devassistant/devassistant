DevAssistant and Docker.io
==========================

*Note: this document is under construction. The described features are not yet implemented
in DevAssistant and might change significantly before version 0.9.0 is released.*

`Docker <http://docker.io>`_ is "an open source project to pack, ship and run any application
as a lightweight container".

A container is basically a lightweight virtual machine, that has all the
dependency installation and system setup done inside it, so they don't
affect your system.

This page summarizes Docker usage workflow during project development/deployment,
as well as instructions on how to make the steps painless through DevAssistant.

Why Docker?
-----------

Development and deployment with Docker, e.g. in a container isolated from your own system,
have several advantages:

* Dependencies are installed only into the container, leaving your system clean.
* System setup is only done inside the container, leaving your system unaffected.
* Your application has a stable runtime environment with a reproducible way of rebuilding
  this environment.
* You can develop/deploy multiple applications with conflicting dependency sets/environment
  settings on one system - just provide a different container for each application.
* You can easily distribute your application as a built container image - and anyone
  can deploy it easily on any system that has Docker.

Terminology
-----------

* **Image** - a file system snapshot that can be "run" as a **container**
* **Container** - a running "lightweight virtual machine" that uses an **image** as its filesystem

It is important to understand that Docker uses layered images. E.g. one image is used as a
*base image* and there can be many images built on top of it - each of them storing
a different set of filesystem changes. When a container is run, Docker "squashes" the images,
creating a single read-only filesystem for the container. All changes done in the container
are recorded into a new image, that can be saved when container shuts down.

Docker Development/Deployment Workflow
--------------------------------------

This section summarizes development and deployment workflows for projects using Docker.

Dockerfile
~~~~~~~~~~

A crucial part of development/deployment workflow is
`Dockerfile <http://docs.docker.io/en/latest/use/builder/>`_. It's basically a list
of instructions that says how to create an image for your application. It contains:

* Name of base image (this is usually obtained from
  `Docker index of images <https://index.docker.io/>`_).
* Zero or more shell commands that install dependencies/set up environment for the application
* List of exported ports (accessible from outside the container), mount points etc.
* A command that copies your application into the image.

Development
~~~~~~~~~~~

Overally, the *development* workflow looks like this (assuming you have a `Dockerfile`):

* Build a fresh image.
* Instead of using source code that was copied into the image statically, mount the source
  directory from your system. This allows you to edit the code outside of the container
  (with your favourite editor/IDE), while running the code inside the container.
* Run the image to get a new container (this is actually done in one command with the
  previous step).

Rough equivalent of the above in Docker commandline invocations::

  docker build -rm <dir> # <dir> is the directory containing Dockerfile
  # -v mounts a local directory to the container, -P opens all ports specified in Dockerfile
  docker run -v <local_path>:<container_path> -P <image_id>

Deployment
~~~~~~~~~~

The *deployment* workflow is quite similar:

* Build a fresh image (from a SCM revision that you want to distribute).
* Distribute the image.

This roughly translates to (if pushing to `Docker index <https://index.docker.io/>`_)::

  docker build <dir>
  docker commit <container_id> myname/myapp
  docker push myname/myapp

Implementation in DevAssistant
------------------------------

DevAssistant 0.9.0 comes with support for building Docker images and running Docker containers.
Currently, the only assistant that supports creating new projects with Dockerfile is
``crt python django``::

  da create python django -n foo --docker

but we also have ``mod docker develop`` assistant, which is generally usable for any type of
project that ships a Dockerfile. Use it like this::

  da modify docker develop [-m MOUNTPOINT] [-i REUSE_IMAGE] [-p PATH]

If used with no arguments, this assistant searches for Dockerfile in current directory,
builds a Docker image, mounts source code (the directory that contains Dockerfile) into it
(mount point is determined based on first found ``ADD`` instruction in Dockerfile), runs
a container and attaches to its output, so that you can develop and see the messages from
process running inside the container.

By using the mentioned options, you can:

- override the directory where your sourcecode should be mounted (``-m``) in the container
- provide an image to use, if you've already built one (``-i``)
- specify path to your project if it's not in your current directory (``-p``)
