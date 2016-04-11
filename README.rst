Pypackage
=========

`View this on GitHub Pages <http://ccpgames.github.io/pypackage/>`__

|Build Status| |Coverage Status| |Version| |Download format| |Downloads
this month| |Development Status| |License| |Gitter Chat|

Pypackage is a collection of python packaging applications including:

::

    py-build
    py-develop
    py-info
    py-install
    py-setup
    py-test

The goal of Pypackage is to make python packaging easier and
faster.

Wouldn't it be nice if you could just write some python, run a command,
and have a distributable package?

Well, now you can!

Features
--------

-  automatic detection of python modules and packages
-  automatic inclusion of non-python package data files, and their
   inclusion in and writing of the ``MANIFEST.in``
-  support for three different testing frameworks (pytest, nose, and
   unittest) for use with ``setup.py test``
-  automatic script detection (any executable file in ``./bin`` or
   ``./scripts``)
-  automatic ``version``, ``author``, ``maintainer`` and ``email`` (s)
   detection (prefers ``__init__.py``, ``__version__.py``)
-  curses front-end to python classifiers selection
-  easy access to package metadata with ``py-info <package>``

Example: "Hello World" application:
-----------------------------------

.. code:: bash

    $ mkdir hello_world
    $ cd hello_world
    $ vim hello_world.py   # write your python here... :)
    $ py-build -is

The ``py-build -is`` command will take you through an interactive
``py-build`` session, and then save the ``setup.py`` to disk (but it
will not run it).

You can use ``py-setup`` at any time to see what Pypackage would use
as a ``setup.py`` in the current directory's context.

Metadata can be mixed in with site-wide defaults from ``$HOME/.pypackage``,
if you want to fill in some common attributes for all your projects.

Pypackage can also find and run your tests with ``python setup.py test``.
It supports three different test runners: pytest, nose, and unittest.

To be clear: pypackage does *not* replace setuptools, pip, or anything
in the python packaging tool-chain; it only attempts to complement those
utilities, and make python packaging a little easier.

In my perfect utopian dream world, I'd see projects not have a ``setup.py``
under source control. Instead there would only be a static metadata file.
In the distribution version of the package, the inverse would be true.

Example, write Python and send it to PyPI
-----------------------------------------

First, `configure your ~/.pypirc
file <https://docs.python.org/2/distutils/packageindex.html#pypirc>`__
with a ``[pypi]`` section if you haven't already. Now, assuming you lay
out your project something like:

::

    ./your_project
    ./your_project/README.md
    ./your_project/pypackage.meta
    ./your_project/...
    ./your_project/your_project/__init__.py
    ./your_project/your_project/your_code.py
    ./your_project/your_project/...

With pypackage installed, from ``./your_project`` run the following
commands to send your project to PyPI for the first time:

.. code:: bash

    $ py-build
    $ py-build -s
    $ python setup.py register
    $ twine upload dist/* || pip install twine && twine upload dist/*

Every time after that, to update your package is a two step process:

.. code:: bash

    $ py-build
    $ twine upload dist/*

This will upload a binary wheel and source distribution to PyPI, so you
can share your work with the world.

The source distribution will include a ``setup.py`` and will not include
the ``pypackage.meta`` if you use one. In this way, Pypackage does not
create a build dependency on your distribution, but rather only on your
source, or perhaps more specifically, your build chain and/or
development environment. (Unless you choose to develop off of the
distributed source version, then carry on doing your thing.)

Just don't submit any patches to the ``setup.py``, because it's not a real
thing in the source. As a project maintainer, you may even consider adding
``setup.py`` to the ``.gitignore`` of your pypackaged projects.

pypackage.meta
--------------

Pypackage uses the ``pypackage.meta`` file in your project to fill in
any details that it would otherwise not be able to guess. It is a JSON
formatted file which can have any of the ``setuptools`` or ``distutils``
setup kwargs as key/value pairs.

It also has a few extra keys to extend the functionality of setuptools (most
notably to support the ``source_label`` and ``source_url`` parameters,
mentioned in `PEP426 <http://legacy.python.org/dev/peps/pep-0426/>`__).

Below is an example of a fully-featured ``pypackage.meta`` file.
(For a complete list of all available keys, they are the ``_KEYS`` and
``_PYPACKAGE_KEYS`` OrderedDicts found in the ``Config`` object;
`view the source
<https://github.com/ccpgames/pypackage/blob/master/pypackage/config.py>`__):

.. code:: meta

    {
        # single line comments like so are allowed in the pypackage.meta
        # but if py-build remakes the meta (-m flag) the comments will be removed

        # name, if not provided, is guessed from the current directory name
        "name": "demo-package",

        # version, if not provided, is searched for in your source code
        "version": "1.0.1",

        # description becomes long_description as well unless long_description is also set
        "description": "This is a demo package",

        # filenames can also be used for long_description, relative path from package root
        "long_description": "README.md",

        "author": "Your name here",
        "author_email": "yourname@yourcompany.com",

        # if author is provided but maintainer is not, maintainer becomes author
        "maintainer": "Someone else",
        "maintainer_email": "someoneelse@yourcompany.com",

        "url": "http://yourcompany.com/yourproject",
        "download_url": "http://yourcompany.com/releases/yourproject",

        # for packages, you can either provide a list of package names, use
        # find_packages() with your own args/kwargs, or use pypackage's defaults.
        # for instance, both of these are valid for packages:
        "packages": ["your_package"],
        # "packages": ["find_packages(exclude=['examples', 'tests'])"],
        # if not provided, this is the default for packages:
        # "packages": ["find_packages(exclude=['test', 'tests'])"],

        # py_modules can be used to install top level python modules, but it will
        # also be guessed at and included if not provided (any top level .py file
        # is included by pypackage's guesswork).
        "py_modules": ["demo_module"],

        # scripts may be provided as relative file paths, or if not provided, pypackage
        # will guess at them. any file in either `bin` or `scripts` directory down
        # from the package root will be included (on windows) or any executable file
        # in those directories are included when building on anything that's not windows.
        "scripts": ["bin/demo_script"],

        # entry_points are the same syntax as you're used to. pypackage makes no guesses at these
        "entry_points": {"paste.app_factory": ["main = demo_package.web:paste"]},

        # a list of packages to be installed when your package is installed
        "install_requires": ["requests > 1.0.0"],

        # a list of packages to be installed when your package is tested
        # note if you're using test_runner you don't have to include the runner or coverage
        "tests_require": ["twisted > 15.0.0"],

        # list of python classifiers. you can run `py-build -R` to forcibly (re)enter
        # the curses classifiers selection process
        "classifiers": [
            "Development Status :: 4 - Beta",
            "Environment :: Web Environment"
        ],

        # ~~ PYPACKAGE ONLY KEYS ~~
        # everything above this was fairly standard, below are pypackage-specific features

        # test_runner can be one of three strings, "nose", "pytest", or "unittest"
        # if provided, pypackage will handle gathering and executing your tests via
        # automatic methods of whatever runner you prefer. to run your tests with
        # a test_runner in use, you can either use `py-test` or `py-build -s` to
        # create the `setup.py` and run `python setup.py test` with that.
        "test_runner": "pytest",

        # tests_dir can be used to provide the directory which contains the tests,
        # if automatic discovery does not work for your layout
        "tests_dir": "tests",

        # runner_args are arguments provided to your test_runner, if you need to
        # use custom flags, perhaps to output a JUnit XML or what have you. Note
        # that if you do provide runner_args that the default runner_args are
        # swapped out in place of what you have provided, no merging occurs.
        "runner_args": ["-vv", "--pdb"],

        # source_label and source_url are described in draft PEP426. they are
        # inserted into the package's metadata, which can be retrieved by using
        # `py-info <package>` on any installed package. the contents are not
        # validated to conform to any spec other than being a string
        "source_label": "5ce507eac031d4e1ccd2c34f7812240ac391d749",

        # same with source_url, it's only in the metadata
        "source_url": "https://yourcompany.com/commit/5ce507eac031d4e1ccd2c34f7812240ac391d749"
    }

Further examples
----------------

If your OS can run a bash script, execute ``demo.sh`` in the top level
of this repo to create a new pypackage venv and some simple example
packages in an ``example`` directory. From there feel free to play
around and experiment with pypackage features and applications.


Screenshots
-----------

The following screenshots were all taken with the ``detected_pkg`` package,
which is created by the ``demo.sh`` script described in the further examples
section above.

Curses top level classifiers selection screen:

.. image:: https://raw.githubusercontent.com/ccpgames/pypackage/gh-pages/images/top_level_post.png
    :alt: top level classifiers
    :align: center

Curses development status screen with ``Beta`` selected:

.. image:: https://raw.githubusercontent.com/ccpgames/pypackage/gh-pages/images/dev_status_post.png
    :alt: development status classifiers
    :align: center

Interactive build process which used the above in its classifiers selection:

.. image:: https://raw.githubusercontent.com/ccpgames/pypackage/gh-pages/images/interactive_build_post.png
    :alt: `py-build -si` interactive build session
    :align: center


Copyright and License
=====================

pypackage was written by Adam Talsma

Copyright (c) 2015 CCP hf.

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be included
in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

.. |Build Status| image:: https://travis-ci.org/ccpgames/pypackage.svg?branch=master
   :target: https://travis-ci.org/ccpgames/pypackage
.. |Coverage Status| image:: https://coveralls.io/repos/ccpgames/pypackage/badge.svg?branch=master
   :target: https://coveralls.io/r/ccpgames/pypackage?branch=master
.. |Version| image:: https://img.shields.io/pypi/v/pypackage.svg
   :target: https://pypi.python.org/pypi/pypackage/
.. |Download format| image:: https://img.shields.io/badge/format-wheel-green.svg?
   :target: https://pypi.python.org/pypi/pypackage/
.. |Downloads this month| image:: https://img.shields.io/pypi/dm/pypackage.svg
   :target: https://pypi.python.org/pypi/pypackage/
.. |Development Status| image:: https://img.shields.io/badge/status-beta-orange.svg
   :target: https://pypi.python.org/pypi/pypackage/
.. |License| image:: https://img.shields.io/github/license/ccpgames/pypackage.svg
   :target: https://pypi.python.org/pypi/pypackage/
.. |Gitter Chat| image:: https://badges.gitter.im/Join%20Chat.svg
   :alt: Join the chat at https://gitter.im/ccpgames/pypackage
   :target: https://gitter.im/ccpgames/pypackage?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge
