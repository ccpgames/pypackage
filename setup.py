"""Pypackage is a collection of python packaging applications including:

    py-build
    py-develop
    py-install
    py-setup
    py-test

The main goal of Pypackage is to make python packaging easier and faster.

Wouldn't it be nice if you could just write some python, run a command, and
have a distributable package? Well now you can!

# Example, "Hello World" application:

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
"""


from setuptools import setup
from setuptools import find_packages
from setuptools.command.test import test as TestCommand


class PyTest(TestCommand):
    """TestCommand subclass to use pytest with setup.py test."""

    def finalize_options(self):
        """Find our package name and test options to fill out test_args."""

        TestCommand.finalize_options(self)
        self.test_args = ["-v", "-rx", "--cov-report", "term-missing", "--cov",
                          "pypackage"]
        self.test_suite = True

    def run_tests(self):
        """pytest discovery and test execution."""

        import pytest
        raise SystemExit(pytest.main(self.test_args))


setup(
    name="pypackage",
    version="0.0.3",
    author="Adam Talsma",
    author_email="se-adam.talsma@ccpgames.com",
    url="http://ccpgames.github.io/pypackage",
    download_url="https://github.com/ccpgames/pypackage",
    description="Pypackage looks to package python without writing a setup.py",
    long_description=__doc__.strip(),
    packages=find_packages(exclude=["test"]),
    package_data={"pypackage": ["pypackage/classifiers"]},
    include_package_data=True,
    install_requires=[
        "wheel      >= 0.24.0",
        "setuptools >= 15.0",
        "pytest     >= 2.7.0",
        "nose       >= 1.3.0",
        "PyYAML     >= 3.0",
    ],
    cmdclass={"test": PyTest},
    tests_require=["pytest", "pytest-cov"],
    entry_points={"console_scripts": [
        "py-build   = pypackage.commands:build",
        "py-develop = pypackage.commands:develop",
        "py-install = pypackage.commands:install",
        "py-setup   = pypackage.commands:setup",
        "py-test    = pypackage.commands:run_tests",
    ]},
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Environment :: Console :: Curses',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Topic :: Software Development',
        'Topic :: Software Development :: Code Generators',
        'Topic :: System :: Archiving :: Packaging',
        'Topic :: System :: Installation/Setup',
        'Topic :: System :: Software Distribution',
        'Topic :: Utilities'
    ],
)
