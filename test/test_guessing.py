"""Tests for pypackages' guessing features."""


import os
import sys
import mock
import pytest
from collections import OrderedDict

from pypackage import guessing
from pypackage.config import Config
from pypackage.cmdline import get_options


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


if __name__ == "__main__":
    pytest.main(["-rx", "-v", "--pdb", __file__])
