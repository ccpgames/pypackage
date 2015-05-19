"""Tests for the install command.

Unfortunately, to make this work with setuptools and pytest and importlib,
we cannot actually install here and import to check for success.

Mock is used to catch and inspect the call to setuptools instead.
"""


import os
import sys
import mock
import pytest
import setuptools

from pypackage.commands import install


def test_simple_module(simple_module):
    """Tests installing a simple python module."""

    with mock.patch.object(setuptools, "setup") as mocked_setup:
        install()

    assert sys.argv == ["setup.py", "install"]
    mod_dir, mod_name = simple_module
    mocked_setup.assert_called_once_with(**{
        "name": os.path.basename(mod_dir),
        "py_modules": [mod_name],
    })


def test_simple_package(simple_package):
    """Tests installing a simple python package."""

    with mock.patch.object(setuptools, "setup") as mocked_setup:
        install()
    assert sys.argv == ["setup.py", "install"]
    mocked_setup.assert_called_once_with(**{
        "name": os.path.basename(simple_package),
        "packages": [os.path.basename(simple_package)],
    })


def test_with_data(with_data):
    """Tests installing a python package with data."""

    with mock.patch.object(setuptools, "setup") as mocked_setup:
        install()
    assert sys.argv == ["setup.py", "install"]
    package = os.path.basename(with_data)
    mocked_setup.assert_called_once_with(**{
        "name": package,
        "packages": [package],
        "package_data": {package: ["{}/data/data_1".format(package)]},
        "include_package_data": True,
    })


def test_with_scripts(with_scripts):
    """Tests installing with scripts."""

    with mock.patch.object(setuptools, "setup") as mocked_setup:
        install()
    assert sys.argv == ["setup.py", "install"]
    package_dir, scripts_dir = with_scripts
    package = os.path.basename(package_dir)
    mocked_setup.assert_called_once_with(**{
        "name": package,
        "packages": [package],
        "scripts": ["{}/my_script".format(scripts_dir)],
    })


if __name__ == "__main__":
    pytest.main(["-rx", "-v", "--pdb", __file__])
