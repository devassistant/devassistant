Contributing to DevAssistant
============================

We are very happy that you want to contribute to DevAssistant, and we want to
make this as easy as possible for you - that's what DevAssistant is all about
anyway. To save both you and ourselves a lot of time and energy, here we list
some rules we would like you to follow to make the pull request process as
quick and painless as possible.

Have a look at our code first
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Every programmer has a different programming style, a different way of
thinking, and that's good. However, if several people contribute to the same
project, and each one of them keeps to their style while ignoring the others,
it becomes very hard to read the code afterwards. Please, before you start
coding your solution, have a look at similar parts of DevAssistant's code to
see how we approached it, and try to follow that if possible. You will make
future maintenance much easier for everyone, and we will be able to review your
pull requests faster as well.


Use PEP8
~~~~~~~~

We follow PEP8, and we ask you to do that as well. It makes the code much more
readable and maintainable. Our only exception is that lines can be as long as
99 characters.


Write tests
~~~~~~~~~~~

Good code has tests. The code you wrote works now, but once someone changes
something, it may all break apart. There are a few general good practices to
go by if you're writing code:

* If you write some new feature, please write tests that make sure it works
  when everything is okay, and that it fails the expected way when it isn't.
* If you fix something, please create tests that ensure that the code really
  works the new way, and that it doesn't work the way it used to work before.

If you go by these rules, there is very little chance that your code breaks
some other part of DevAssistant, and at the same time, you make your part of
code less likely to break in the future.

For testing, we use `pytest <http://pytest.org/latest/contents.html#toc>`_.


When testing, use mocking (namely flexmock)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Often when you need to test some object's behaviour, you need to "pretend" that
something works somehow, for example that the network is up or that a specific
file exists. That is okay, but it is not okay to actually connect to the
internet for testing, or create or delete specific files in the file system.
This could break something, or might not work on our test server.

Of course, sometimes you may need to create a nameless temporary file with
``tempfile.mkstemp()``, which is something we do often, and it is a perfectly
acceptable practice. However, you should not touch for example the
``~/.devassistant/config`` file, which actually belongs to the user, and by
writing it, you could delete or damage the user's config.

To overcome these problems, we are using flexmock, which is a library that
allows you to modify the behaviour of the environment so that you don't have
to rely on the values on the user's machine. By calling flexmock on an object,
you can either change some of its methods or attributes, or you can completely
replace it with a flexmock object whose behaviour you fully control.

An example::

    import os
    from flexmock import flexmock

    def test_something(self):
        flexmock(os.path).should_receive('isfile').with_args('/foo/bar/baz').and_return(True)
        do_something_assuming_foobarbaz_is_a_valid_file()

What you did here is modify the behaviour of the method ``os.path.isfile()`` so
that it returns ``True`` when called with the argument ``/foo/bar/baz``. This
works only within the current code block, so you can mock something in one
test, and then just forget about it. The next test will have clean environment
again.

Here is `flexmock documentation <http://has207.github.io/flexmock/user-guide.html>`_.

Just a note here: Mocking doesn't work well in setup and teardown methods,
because they are different code blocks.


Parameterize tests
^^^^^^^^^^^^^^^^^^

It makes perfect sense to feed multiple values to a method to see how it works
in different situations. Very often it's done like this::

    def test_something(self):
        for value, number in [('foo', 1), ('bar', 2), ('baz', 3)]:
            do_something(value, number)

That's not exactly how we want to do it. For one, if it fails, you can't
quickly see what the values were when the test failed, so you have to use a
debugger or put some print statements in the code. Another thing is that it's
harder to read and more prone to error. The preferred way of achieving the same
functionality is this::

    @pytest.mark.parametrize(('value', 'number'), [
        ('foo', 1),
        ('bar', 2),
        ('baz', 3),
    ])
    def test_something(self, value, number):
        do_something(value, number)

The second example is much better especially if you're doing more than just
calling one method - for example mocking, running a setup/teardown method etc.
Pytest also automatically outputs the test parameters if a test fails, so
debugging is much easier. We strongly encourage you to use the second example,
and might not accept your pull request if you don't, unless you present a good
reason why.


Use six for Python 2 + 3 compatibility
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

DevAssistant works with both major versions of Python currently in production,
and we want to keep only one codebase, therefore we need an interoperability
library, namely ``six``. This library is much more powerful and easy to use
than, say, importing `__future__`, so please, use ``six`` and nothing else.

In a majority of cases, we use ``six`` for these things:

* importing libraries that were moved or renamed
* testing if a variable contains a string/unicode/bytes
* testing what version of python DevAssistant is running on.

To import a library that was renamed in Python 3, you use the
``six.moves.builtins`` module::

    from six.moves.builtins import urllib

This imports a module mimicking Python 3's `urllib` module, so both in Python 2
and Python 3, you then call::

    urllib.request.urlretrieve(url)

The variable containing the information if the code is running under Python 3
is found here::

    import six
    six.PY3

There is also the ``six.PY2`` constant, but that was added to ``six`` quite
recently, so for better backwards compatibility, we kindly ask you to use ``not
six.PY3`` instead.


Use pyflakes to sanitize your code
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Pyflakes (as well as pylint), are two great tools for improving the quality of
your code. We especially urge you to use pyflakes to find unused imports,
undeclared variables and other errors detectable without actually running the
code.


Always `talk to us <https://devassistant.org/contact>`_ when:
~~~~~~~~~~~~~~~~~~~~~~~

Your contribution changes dependencies
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

We try to keep DevAssistant's dependency chain as small as possible, so if your
code adds a dependency, it is a big deal for us. For this reason, we urge you
to talk to us first (`here's how <https://devassistant.org/contact>`_). If we
decide that the new dependency is necessary, we'll gladly give you a green
light and accept your contribution. If we think that your idea can do without
adding the new package, we'll do our best to help you modify your idea.

However, if you do not talk to us and implement your feature right away, there
is a risk that we will reject your contribution and you will have to throw your
existing code away and start from scratch.


You want to implement a large feature
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

We welcome large contributions, and are very happy that you take the interest
and time to make them. However, we have certain plans where DevAssistant should
go, or what it should look like, and there's quite a good chance that if you
don't discuss your idea with us, you might write something quite different,
which we won't be willing to accept.

To avoid this kind of situations, always consult your intentions with us before
you start coding - we're more than open to new ideas, but we want to know about
them first.


You want to include your contribution in an upcoming release
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

We do have a release plan, but this doesn't mean we couldn't occasionally wait
a few days for your feature to be included. If you tell us about your
contribution, and we decide that we want it in, we'll hold a release for you to
finish and submit your code. Of course, the sooner you tell us, the better the
outcome will be.

