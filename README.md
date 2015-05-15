# Pypackage

[View this on GitHub Pages](http://ccpgames.github.io/pypackage/)

[![Build Status](https://travis-ci.org/ccpgames/pypackage.png?branch=master)](https://travis-ci.org/ccpgames/pypackage)
[![Coverage Status](https://coveralls.io/repos/ccpgames/pypackage/badge.svg?branch=master)](https://coveralls.io/r/ccpgames/pypackage?branch=master)
[![Version](https://img.shields.io/pypi/v/pypackage.svg)](https://pypi.python.org/pypi/pypackage/)
[![Download format](https://img.shields.io/badge/format-wheel-green.svg?)](https://pypi.python.org/pypi/pypackage/)
[![Downloads this month](https://img.shields.io/pypi/dm/pypackage.svg)](https://pypi.python.org/pypi/pypackage/)
[![Development Status](https://img.shields.io/badge/status-beta-orange.svg)](https://pypi.python.org/pypi/pypackage/)
[![License](https://img.shields.io/github/license/ccpgames/pypackage.svg)](https://pypi.python.org/pypi/pypackage/)

Pypackage is a collection of python packaging applications including:

    py-build
    py-develop
    py-install
    py-setup
    py-test

The main goal of Pypackage is to make python packaging easier and faster.

Wouldn't it be nice if you could just write some python, run a command, and
have a distributable package? Well now you can!

## Example, "Hello World" application:

```bash
$ mkdir hello_world
$ cd hello_world
$ vim hello_world.py   # write your python here... :)
$ py-build -is
```

The `py-build -is` command will take you through an interactive py-build
session and save the setup.py to disk after creating it, but will not run it.

You can also use the `py-setup` command at any time to print what Pypackage
would use as a setup.py in the current directory's context.

Metadata can be mixed in with site-wide defaults from $HOME/.pypackage if you
want to fill in some common attributes for all your projects.

Pypackage also provides three different test runners to automatically find and
run your tests with `python setup.py test`, you can use any of pytest, nose or
unittest.

To be clear though: pypackage does not intend on replacing setuptools, pip, or
really anything at all in the python packaging tool-chain, it only attempts to
compliment those utilities and make getting started with python packaging a
little easier.

In my utopian perfect dream world, I'd see projects not having a setup.py under
source control, instead only a static metadata file, then having the inverse
relationship being true in the distribution version of the package.


# Copyright and License

pypicloud-tools was written by Adam Talsma

Copyright (c) 2015 CCP hf.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
