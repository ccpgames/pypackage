"""Tests for the pypackage_setup function in the __init__.py."""


import sys
import mock
import pytest

import pypackage
from pypackage import pypackage_setup


@pytest.mark.parametrize("flag", ("-h", "--help"))
def test_help_is_raised(reset_sys_argv, flag):
    """Ensure additional help is shimmed inside the help msg per function."""

    sys.argv = ["py-build", flag]
    with pytest.raises(SystemExit) as error:
        pypackage_setup(additional="super important information")
    assert "super important information" in error.value.args[0]


@pytest.mark.parametrize("flag", ("-v", "--version"))
def test_version_is_raised(reset_sys_argv, flag):
    """Ensure the version info is raised with SystemExit when requested."""

    sys.argv = ["py-build", flag]
    with pytest.raises(SystemExit) as error:
        pypackage_setup()
    assert error.value.args[0] == pypackage.VERSION


@pytest.mark.parametrize("flag", ("-i", "--interactive"))
def test_interactive_setup_called(capfd, simple_module, reset_sys_argv, flag):
    """Ensure we call run_interactive_setup when requested."""

    sys.argv = ["py-build", "-N", flag]
    with mock.patch.object(pypackage, "run_interactive_setup") as inter_patch:
        pypackage_setup()

    assert inter_patch.call_count == 1

    out, err = capfd.readouterr()
    assert "~ setup.py ~" in out
    assert "from setuptools import setup" in out
    assert "setup(" in out
    assert not err


@pytest.mark.parametrize("flag", ("-R", "--reclassify"))
def test_reclassify_trigger(simple_module, reset_sys_argv, flag):
    """Ensure set_value_in_config is called for classifiers if requested."""

    sys.argv = ["py-build", "-N", flag]
    with mock.patch.object(pypackage, "set_value_in_config") as set_v_patch:
        pypackage_setup()

    assert set_v_patch.call_count == 1


if __name__ == "__main__":
    pytest.main(["-rx", "-v", "--pdb", __file__])
