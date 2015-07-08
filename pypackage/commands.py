"""Entry points for running setup.py commands.

Each command's docstring is used as additional help if the -h flag is used.

Setup is a bit of a snowflake in that it doesn't build anything, takes no args.

Info does not take any arguments, only looks up packages by name.
"""


from __future__ import print_function

import sys
import pkg_resources

from . import pypackage_setup
from .config import get_config
from .cmdline import get_options
from .cmdline import help_and_version


def install():
    """py-install will build a setup.py and use it to install locally."""

    pypackage_setup(["install"], additional=install.__doc__)


def run_tests():
    """py-test will build a setup.py and run the test command with it.

    It is recommended to supply a 'test_runner' argument in your metadata to
    use this command. Setting it to one of "pytest", "nose", or "unittest" will
    cause this command to execute a test discovery and execution. You can also
    specify the "tests_dir" if you find the test runner is unable to find your
    tests. The "runner_args" key is set per runner to values that include some
    level of verbosity and coverage statistics, but feel free to override that
    value in your packages' metadata file to something more your liking.

    Note that pytest and nosetest do not expect __init__.py files in your test
    directories, whereas unittest requires them to find the tests.\
    """

    pypackage_setup(["test"], additional=run_tests.__doc__)


def develop():
    """py-develop will build a setup.py and run the develop command with it."""

    pypackage_setup(["develop"], additional=develop.__doc__)


def build():
    """py-build will build and run a setup.py from metadata and/or inspection.

    After running py-build you should have a dist directory containing a new
    source release and wheel release which you could then upload to pypi and/or
    install with pip.

    If you only want to build the metadata/setup.py and not the package itself,
    which can be handy during development, use one of the -s or -m flags.\
    """

    options = get_options()
    build_commands = ["build", "sdist", "bdist_wheel"]
    if options.setup or options.metadata:
        # don't run the setup.py, just build it and/or remake the metadata
        build_commands = None
    pypackage_setup(build_commands, options=options, additional=build.__doc__)


@help_and_version
def setup():
    """py-setup will create a setup.py from metadata files and/or inspection.

    It only prints this configuration to stdout, it does not run the setup.py,
    do any guesswork/inspection, or even save it to disk (py-build does that).

    You can use this command to test how changes in your metadata translate to
    changes in the setup.py.

    Usage:
        py-setup [FILEPATH]

    positional arguments:
        FILEPATH    Metadata directory location (default: cwd)\
    """

    if len(sys.argv) >= 2:
        for arg in sys.argv[1:]:
            print(get_config(arg))
    else:
        print(get_config())


@help_and_version
def info():
    """py-info will print the most recent version of a package's metadata.

    Usage:
        py-info <package> [package] ...\
    """

    env = pkg_resources.Environment()
    separator = False
    for arg in sys.argv[1:]:
        try:
            pkg = env[pkg_resources.safe_name(arg)][0]
        except IndexError:
            print(
                "The package {} was not found.".format(arg),
                file=sys.stderr,
            )
            continue

        # this is what a decade of legacy code looks like
        if pkg.PKG_INFO == "METADATA":
            # don't look too close, this is an email message object...
            meta = pkg._parsed_pkg_info.items()
            print("{}{}".format(
                "{}\n".format("-" * 40) if separator else "",
                "\n".join([
                    "{}: {}".format(k, v) for k, v in meta if v != "UNKNOWN"
                ]),
            ))
        else:
            # this one's a string generator
            meta = pkg._get_metadata("PKG-INFO")
            print("{}{}".format(
                "{}\n".format("-" * 40) if separator else "",
                "\n".join([
                    line for line in meta if "UNKNOWN" not in line
                ])
            ))

        separator = True
