"""Tests to cover the logic in the command line entry points."""


import sys
import mock
import pytest

import pypackage
from pypackage import commands


def test_run_tests():
    """Ensure we call tests correctly..."""

    with mock.patch.object(commands, "pypackage_setup") as patched_setup:
        commands.run_tests()

    patched_setup.assert_called_once_with(
        ["test"],
        additional=commands.run_tests.__doc__,
    )


def test_run_develop():
    """Ensure we call setup.py develop correctly..."""

    with mock.patch.object(commands, "pypackage_setup") as patched_setup:
        commands.develop()

    patched_setup.assert_called_once_with(
        ["develop"],
        additional=commands.develop.__doc__,
    )


@pytest.mark.parametrize("flag", ("s", "m"), ids=("setup", "metadata"))
def test_no_build(reset_sys_argv, flag):
    """Ensure build is not called if setup or metadata is requested."""

    sys.argv = ["py-build", "-{}".format(flag)]
    opts = mock.Mock()  # mock object attributes respond as True-ish
    with mock.patch.object(commands, "pypackage_setup") as patched_setup:
        with mock.patch.object(commands, "get_options", return_value=opts):
            commands.build()

    patched_setup.assert_called_once_with(
        None,
        additional=commands.build.__doc__,
        options=opts,
    )


def test_setup_entry(reset_sys_argv):
    """Setup's entry is a bit different."""

    sys.argv = ["py-setup"]
    with mock.patch.object(commands, "get_config") as patched_config:
        commands.setup()
    patched_config.assert_called_once_with()


@pytest.mark.parametrize("flag", ("-h", "--help"))
def test_setup_entry__help(reset_sys_argv, flag):
    """Ensure we get the docstring as exit help if the flag is set."""

    sys.argv = ["py-setup", flag]
    with pytest.raises(SystemExit) as patched_exit:
        commands.setup()

    for line in commands.setup.__doc__.splitlines():
        line = line.strip()
        if line:
            assert line in patched_exit.value.args[0]


@pytest.mark.parametrize("flag", ("-v", "--version"))
def test_setup_entry__version(reset_sys_argv, flag):
    """Ensure the VERSION static is raised with SystemExit when requested."""

    sys.argv = ["py-test", flag]
    with pytest.raises(SystemExit) as patched_exit:
        commands.setup()

    assert patched_exit.value.args[0] == pypackage.VERSION


def test_setup_entry__location(reset_sys_argv):
    """Any additonal arguments should be treated as a filepath."""

    sys.argv = ["py-test", "somewhere/on/your/fs"]
    with mock.patch.object(commands, "get_config") as patched_config:
        commands.setup()

    patched_config.assert_called_once_with("somewhere/on/your/fs")


def test_setup_entry__multilocations(reset_sys_argv):
    """All additonal arguments should be treated as a filepath."""

    sys.argv = ["py-test", "place1", "place2"]
    with mock.patch.object(commands, "get_config") as patched_config:
        commands.setup()

    patched_config.assert_any_call("place1")
    patched_config.assert_any_call("place2")

    assert patched_config.call_count == 2


def test_info(reset_sys_argv, capfd):
    """Ensure we're looking up and dumping package metadata to stdout."""

    sys.argv = ["py-info", "pytest"]
    commands.info()
    stdout, stderr = capfd.readouterr()

    assert not stderr
    assert "Name: pytest" in stdout
    assert "License: MIT license" in stdout


def test_info__pkg_not_found(reset_sys_argv, capfd):
    """Ensure the error message when a package is not found."""

    sys.argv = ["py-info", "some-random-non-existant-package"]
    commands.info()
    out, err = capfd.readouterr()

    assert not out
    assert "The package some-random-non-existant-package was not found." in err


def test_info__using_pkg_info(reset_sys_argv, capfd):
    """Verify the metadata when using older-style lookups."""

    def metadata_generator():
        """Mock metadata generator."""
        for line in [
            "Metadata-Version: 1.0",
            "Version: 1.0.0",
            "Source-label: somewords",
            "Source-url: http://yourcompany.com",
        ]:
            yield line
        raise StopIteration

    mock_pkg = mock.Mock()
    mock_pkg.PKG_INFO = "PKG-INFO"
    mock_pkg._get_metadata = mock.Mock(return_value=metadata_generator())

    mockenv = mock.Mock()
    mockenv.__getitem__ = mock.Mock(return_value=[mock_pkg])

    environment_patch = mock.patch.object(
        commands.pkg_resources,
        "Environment",
        return_value=mockenv,
    )

    sys.argv = ["py-info", "foo-bar"]
    with environment_patch:
        commands.info()

    out, err = capfd.readouterr()
    assert not err
    for line in metadata_generator():
        assert line in out


if __name__ == "__main__":
    pytest.main(["-rx", "-v", "--pdb", __file__])
