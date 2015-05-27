# coding: utf-8
"""Tests for pypackages' guessing features."""


from __future__ import unicode_literals

import io
import os
import sys
import mock
import time
import codecs
import pytest
import random
from collections import OrderedDict

from pypackage import guessing
from pypackage.config import Config
from pypackage.cmdline import get_options


def random_text(length):
    """Returns a random lower-case string of len length."""

    return "".join([
        chr(random.sample(range(97, 123), 1)[0]) for _ in range(length)
    ])


def test_ignored_data_files(with_data):
    """Ensure that files in ignored directories are ignored."""

    root, pkg_root = with_data
    os.mkdir(os.path.join(pkg_root, "build"))
    with open(os.path.join(pkg_root, "build", "data"), "w") as opendata:
        opendata.write("some data")

    data_files = guessing.potential_data_files([])
    expected = [os.path.join(os.path.basename(pkg_root), "data", "data_1")]
    assert data_files == expected


def test_perform_guesswork(capfd, reset_sys_argv, move_home_pypackage):
    """Ensure the user can deselect guesses when using interactive."""

    conf = Config()
    conf.name = "previously existing"
    sys.argv = ["py-build", "-i"]
    guesses = OrderedDict([
        ("name", "some name"),
        ("py_modules", "some_thing"),
        ("scripts", ["bin/something"]),
        ("package_data", ["thing/data/file_1"]),
    ])

    with mock.patch.object(guessing, "_guess_at_things", return_value=guesses):
        with mock.patch.object(guessing, "INPUT",
                               side_effect=iter(["1", "-3", "2", ""])):
            guessing.perform_guesswork(conf, get_options())

    assert conf.name == "previously existing"
    assert not hasattr(conf, "py_modules")
    assert conf.package_data == {"previously existing": ["thing/data/file_1"]}
    assert conf.scripts == ["bin/something"]

    out, err = capfd.readouterr()
    assert "name will not be guessed" in out
    assert "py_modules will not be guessed" in out

    assert not err


def test_perform_guesswork__ignore(capfd, reset_sys_argv, move_home_pypackage):
    """If the user responds with 'all', ignore all guesses."""

    conf = Config()
    conf.name = "previously existing"
    sys.argv = ["py-build", "-i"]
    guesses = OrderedDict([
        ("name", "some name"),
        ("py_modules", "some_thing"),
        ("scripts", ["bin/something"]),
        ("package_data", {"some name": ["thing/data/file_1"]}),
    ])

    with mock.patch.object(guessing, "_guess_at_things", return_value=guesses):
        with mock.patch.object(guessing, "INPUT", return_value="all"):
            guessing.perform_guesswork(conf, get_options())

    assert conf.name == "previously existing"
    assert not hasattr(conf, "py_modules")
    assert not hasattr(conf, "package_data")
    assert not hasattr(conf, "scripts")

    out, err = capfd.readouterr()
    assert "ignoring all guesses" in out
    assert not err


@pytest.mark.parametrize(
    "side_effect",
    (KeyboardInterrupt, EOFError),
    ids=("^C", "^D"),
)
def test_perform_guesswork__interrupts(reset_sys_argv, side_effect):
    """Ensure the user can cleanly exit the interactive session."""

    sys.argv = ["py-build", "-siR"]
    guesses = {"fake": True}
    with mock.patch.object(guessing, "_guess_at_things", return_value=guesses):
        with mock.patch.object(guessing, "INPUT", side_effect=side_effect):
            with pytest.raises(SystemExit) as error:
                guessing.perform_guesswork(Config(), get_options())

    assert error.value.args[0] == "\nInterrupted"


def test_latest_git_tag(simple_package):
    """If the project is under git control and has tags, return the newest."""

    os.mkdir(".git")
    os.mkdir(os.path.join(".git", "refs"))
    os.mkdir(os.path.join(".git", "refs", "tags"))

    for i in range(2):
        if i:
            time.sleep(1.1)

        name = random_text(6)
        contents = random_text(40)
        with open(os.path.join(".git", "refs", "tags", name), "w") as opentag:
            opentag.write(contents)

    assert guessing.find_in_files()["version"] == name


@pytest.fixture
def find_in_files_setup(simple_package):
    """Writes user data to simple_package's __init__.py."""

    pkg_name = os.path.basename(simple_package)
    pkg_root = os.path.join(simple_package, pkg_name)
    init_file = os.path.join(pkg_root, "__init__.py")
    with io.open(init_file, "w", encoding="utf-8") as openinit:
        openinit.writelines([
            "__author__='mike tyson'\n",
            "__email__  =  'irðn@mike.com'\n",
            '_version_=    "1.0.0-final"\n',
            "maintainer = 'don king'\n",
            "maintainer_email = 'don@king.com'\n",
        ])

    return simple_package, pkg_root


def find_in_files_asserts(results):
    """Assert the result set contains the setup information."""

    assert results["author"] == "mike tyson"
    assert results["author_email"] == "irðn@mike.com"
    assert results["version"] == "1.0.0-final"
    assert results["maintainer"] == "don king"
    assert results["maintainer_email"] == "don@king.com"


def test_find_in_files(find_in_files_setup):
    """Write some attribute data to package files and find them."""

    find_in_files_asserts(guessing.find_in_files())


def test_find_in_files__ignored_dir(find_in_files_setup):
    """Ensure data is not considered from ignored directories."""

    ignored_dir = os.path.join(find_in_files_setup[0], "other-pkg.egg")
    os.mkdir(ignored_dir)
    with open(os.path.join(ignored_dir, "__init__.py"), "w") as openinit:
        openinit.write("\n".join([
            "__author__ = 'mohammad ali'",
            "__email__ = 'mo@ali.com'",
            '__version__ = "2.0.0-beta"',
        ]))

    find_in_files_asserts(guessing.find_in_files())


def test_find_in_files__binary_skip(find_in_files_setup):
    """Ensure files that we cannot decode are skipped over."""

    version_file = os.path.join(find_in_files_setup[1], "__version__.py")
    with open(version_file, "wb") as openversionfile:
        openversionfile.write(codecs.encode("__author__ = 'bob'\n", "utf-8"))
        openversionfile.write(codecs.encode("__version__ = '", "utf-8"))
        openversionfile.write(os.urandom(1024))
        openversionfile.write(codecs.encode("'\n", "utf-8"))

    find_in_files_asserts(guessing.find_in_files())


def test_find_in_files__file_too_large(find_in_files_setup):
    """Ensure files that are too large are ignored."""

    # if this file isn't ignored for size, it'll have a higher weight than
    # the data in __init__.py. it's also just over the limit for size
    version_file = os.path.join(find_in_files_setup[1], "__version__.py")

    with open(version_file, "w") as openversionfile:
        openversionfile.write("__author__ = 'bob'\n")
        for _ in range(100):
            openversionfile.write("{}\n".format(random_text(1024)))

    find_in_files_asserts(guessing.find_in_files())


if __name__ == "__main__":
    pytest.main(["-rx", "-v", "--pdb", __file__])
