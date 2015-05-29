"""Constants used in pypackage."""


import os
import sys
import pkg_resources


if sys.version_info > (3,):  # pragma: no cover
    INPUT = input
    STRING_TYPE = str
    CHECKMARK = chr(0x2713)
else:  # pragma: no cover
    INPUT = raw_input           # nopep8
    STRING_TYPE = basestring    # nopep8
    CHECKMARK = unichr(0x2713)  # nopep8


VERSION = "{} {}".format(
    os.path.basename(sys.argv[0]),
    pkg_resources.get_distribution("pypackage").version,
)


META_NAME = "pypackage.meta"


HELP = """Pypackage is an interactive and automatic Python packaging tool.

Package metadata comes from three sources (overridden in order):

    1) Site defaults, located in $HOME/.pypackage. These are applied to every
       package you make, and should be constrained to generic attributes such
       as author, emails, etc.
    2) Guesswork, done internally in pypackage. It will make guesses for what
       python modules or packages you have, your package name, scripts and/or
       static data to include.
    3) Package metadata. Read from the current directory's {}, this
       JSON-ish (full line comments are allowed/ignored) file can contain keys
       for every/any kwarg that either setuptools or distutils can handle.

Pypackage uses setuptools to perform any installation or building of packages.

{{additional}}

Usage:
    {} [OPTIONS]

Options:
    -a --all                Same as -e/--extended, display all config options
    -e --extended           Consider all options for interactive configuration
    -h --help               Show this help message and exit
    -i --interactive        Enter interactive configuration mode
    -m --metadata           Only update the package metadata; build a setup.py
    -N --no-guess           Do not perform any guessing of attributes
    -p --reprobe            Re-guess all attributes, ignore package metadata
    -r --reset --rebuild    Rebuild package metadata, ignore current settings
    -R --reclassify         (re)Enter the classifiers selection screen
    -s --setup              Only build a setup.py; don't run it
    -v --version            Show version information and exit\
""".format(
    META_NAME,
    os.path.basename(sys.argv[0]),
)
