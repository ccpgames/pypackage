"""Tests to cover the logic in the command line entry points."""


import sys
import mock
import pytest

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

    assert patched_exit.value.args[0] == commands.VERSION


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


if __name__ == "__main__":
    pytest.main(["-rx", "-v", "--pdb", __file__])
