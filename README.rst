Pypackage
=========

`View this on GitHub Pages <http://ccpgames.github.io/pypackage/>`__

|Build Status| |Coverage Status| |Version| |Download format| |Downloads
this month| |Development Status| |License|

Pypackage is a collection of python packaging applications including:

::

    py-build
    py-develop
    py-install
    py-setup
    py-test

The main goal of Pypackage is to make python packaging easier and
faster.

Wouldn't it be nice if you could just write some python, run a command,
and have a distributable package? Well now you can!

Features
--------

-  automatic python modules and packages detection
-  automatic inclusion of non-python package data files, and their
   inclusion in and writing of the MANIFEST.in
-  support for three different testing frameworks (pytest, nose, and
   unittest) for use with ``setup.py test``
-  automatic script detection (any executable file in ./bin or ./scripts)
-  automatic version, author, maintainer and email(s) detection (perfers
   __init__.py, __version__.py)
-  curses front-end to python classifiers selection

Example, "Hello World" application:
-----------------------------------

.. code:: bash

    $ mkdir hello_world
    $ cd hello_world
    $ vim hello_world.py   # write your python here... :)
    $ py-build -is

The ``py-build -is`` command will take you through an interactive
py-build session and save the setup.py to disk after creating it, but
will not run it.

You can also use the ``py-setup`` command at any time to print what
Pypackage would use as a setup.py in the current directory's context.

Metadata can be mixed in with site-wide defaults from $HOME/.pypackage
if you want to fill in some common attributes for all your projects.

Pypackage also provides three different test runners to automatically
find and run your tests with ``python setup.py test``, you can use any
of pytest, nose or unittest.

To be clear though: pypackage does not intend on replacing setuptools,
pip, or really anything at all in the python packaging tool-chain, it
only attempts to complement those utilities and make getting started
with python packaging a little easier.

In my utopian perfect dream world, I'd see projects not having a
setup.py under source control, instead only a static metadata file, then
having the inverse relationship being true in the distribution version
of the package.

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

This will upload a binary wheel and source distribution to PyPI so you
can share your work with the world.

The source distribution will include a ``setup.py`` and will not include
the ``pypackage.meta`` if you use one. In this way, Pypackage does not
create a build dependency on your distribution, but rather only on your
source, or perhaps more specifically, your build chain and/or
development environment. Unless you choose to develop off of the
distributed source version, then carry on doing your thing. Just don't
submit any patches to the ``setup.py`` because it's not a real thing in
the source. As a project maintainer, you may even consider adding
``setup.py`` to the ``.gitignore`` of your pypackaged projects.

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

Interactive build process which used the above in it's classifiers selection:

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
