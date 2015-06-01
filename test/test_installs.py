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
    root, pkg_root = with_data
    package = os.path.basename(pkg_root)
    mocked_setup.assert_called_once_with(**{
        "name": package,
        "packages": [package],
        "package_data": {package: ["{}/data/data_1".format(package)]},
        "include_package_data": True,
        "long_description": "this package has data!",
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


def test_long_description_as_file(with_readme):
    """Test installing with a filepath as a long_description."""

    with mock.patch.object(setuptools, "setup") as mocked_setup:
        install()
    assert sys.argv == ["setup.py", "install"]
    package_dir, mod_root = with_readme
    package = os.path.basename(mod_root)
    mocked_setup.assert_called_once_with(**{
        "name": package,
        "packages": [package],
        "long_description": "{n}\n{d}\n\n{n}'s readme... with content!".format(
            n=package,
            d="=" * len(package),
        ),
        "package_data": {package: ['README']},
        "include_package_data": True,
    })


if __name__ == "__main__":
    pytest.main(["-rx", "-v", "--pdb", __file__])
