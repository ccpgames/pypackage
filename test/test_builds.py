"""Create and inspect python packages built with pypackage."""


import os
import sys
import glob
import codecs
import pytest
import tarfile
import zipfile

from pypackage.commands import build


def verify_wheel(expected, zip_path):
    """Asserts the standard wheel files and `expected` are in the zip."""

    wheel_zip = zipfile.ZipFile(glob.glob(os.path.join(zip_path, "*.whl"))[0])
    wheel_files = [zipf.filename for zipf in wheel_zip.infolist()]

    for expected_file in expected:
        for wheel_file in wheel_files:
            if wheel_file.endswith(expected_file):
                break
        else:
            pytest.fail("{} not found in wheel!".format(expected_file))

    standard_wheel_files = ["DESCRIPTION.rst", "WHEEL", "METADATA", "RECORD",
                            "metadata.json", "top_level.txt"]
    assert len(wheel_files) == len(expected) + len(standard_wheel_files)

    for std_file in standard_wheel_files:
        for file_ in wheel_files:
            if os.path.sep in file_:
                if std_file == os.path.split(file_)[1]:
                    break
        else:
            pytest.fail("{} not found in wheel?".format(std_file))


def verify_source(source_files, gz_path):
    """Ensure the std python dist files and source_files are in the .tar.gz."""

    f_name = glob.glob(os.path.join(gz_path, "*.tar.gz"))[0]
    with tarfile.open(f_name, "r:gz") as tar_file:
        tar_files = tar_file.getnames()

    pkg_full_name = os.path.basename(
        os.path.dirname(gz_path)
    ).split(".tar.gz")[0]
    egg_name = "{}.egg-info".format(pkg_full_name.rsplit("-")[0])  # fragile..
    source_files.extend([
        "PKG-INFO",
        egg_name,
        os.path.join(egg_name, "dependency_links.txt"),
        os.path.join(egg_name, "PKG-INFO"),
        os.path.join(egg_name, "SOURCES.txt"),
        os.path.join(egg_name, "top_level.txt"),
        "setup.cfg",
        "setup.py",
    ])
    assert len(tar_files) == len(source_files) + 1  # +1 for the base dir
    base_dir_skipped = False
    for tar_file in tar_files:
        assert tar_file.startswith(pkg_full_name)
        if os.path.sep in tar_file:
            tar_file = tar_file[tar_file.index(os.path.sep) + 1:]
            assert tar_file in source_files
        elif not base_dir_skipped:
            base_dir_skipped = True
        else:
            pytest.fail("{} not expected in source dist!".format(tar_file))


def verify_artifacts(mod_dir):
    """Asserts the dist directory exists and has two files in it."""

    dist_dir = os.path.join(mod_dir, "dist")
    assert os.path.isdir(dist_dir)
    assert len(os.listdir(dist_dir)) == 2, "should have wheel and src"
    return dist_dir


def test_simple_module(simple_module):
    """Test a single simple python module."""

    build()

    mod_dir, mod_name = simple_module
    dist_dir = verify_artifacts(mod_dir)

    mod_file = "{}.py".format(mod_name)
    verify_wheel([mod_file], dist_dir)
    verify_source([mod_file], dist_dir)


def test_simple_package(simple_package):
    """Ensure a simple normal python package is correctly built."""

    build()
    dist_dir = verify_artifacts(simple_package)

    package_name = os.path.basename(simple_package)
    expected_files = [
        "{}/__init__.py".format(package_name),
        "{}/my_module.py".format(package_name),
    ]

    verify_wheel(expected_files, dist_dir)
    verify_source(expected_files + [package_name], dist_dir)


def test_with_data(with_data):
    """Ensure the non-python data files are being picked up."""

    build()
    root, pkg_root = with_data
    dist_dir = verify_artifacts(root)

    package_name = os.path.basename(pkg_root)
    expected_files = [
        "{}/data/data_1".format(package_name),
        "{}/__init__.py".format(package_name),
        "{}/my_module.py".format(package_name),
    ]
    expected_in_source = expected_files + [
        "{}/data".format(package_name),  # data folder
        "MANIFEST.in",
        package_name,  # base folder
    ]

    verify_wheel(expected_files, dist_dir)
    verify_source(expected_in_source, dist_dir)


def test_manifest_mixin(with_data):
    """Ensure we can write a partial MANIFEST.in file."""

    root, pkg_root = with_data
    pkg_name = os.path.basename(pkg_root)
    with open(os.path.join(pkg_root, "data", "data_2"), "w") as opendata:
        opendata.write("some data")

    with open(os.path.join(root, "MANIFEST.in"), "w") as openmanifest:
        openmanifest.write("include {}/data/data_2\n".format(pkg_name))

    build()
    dist_dir = verify_artifacts(root)

    tar_fname = glob.glob(os.path.join(dist_dir, "*.tar.gz"))[0]
    with tarfile.open(tar_fname, "r:gz") as tar_file:
        tar_file.getnames()
        manifest = [f for f in tar_file.members if "MANIFEST.in" in f.name][0]
        content = tar_file.extractfile(manifest).read()

        assert [codecs.decode(l, "utf-8") for l in content.splitlines()] == [
            "include {}/data/data_2".format(pkg_name),
            "include {}/data/data_1".format(pkg_name),
        ]


def test_with_scripts(with_scripts):
    """Ensure the executable scripts are being included."""

    package_dir, script_dir = with_scripts
    build()
    dist_dir = verify_artifacts(package_dir)

    package_name = os.path.basename(package_dir)
    expected_in_wheel = [
        "/scripts/my_script",
        "{}/__init__.py".format(package_name),
        "{}/my_module.py".format(package_name),
    ]
    expected_in_source = [
        package_name,  # base folder
        script_dir,
        "{}/my_script".format(script_dir),
        "{}/__init__.py".format(package_name),
        "{}/my_module.py".format(package_name),
    ]

    verify_wheel(expected_in_wheel, dist_dir)
    verify_source(expected_in_source, dist_dir)


def test_only_binary(only_binary):
    """Packages without any python at all should have data_files installed."""

    package_dir, binary_file = only_binary
    build()
    dist_dir = verify_artifacts(package_dir)

    verify_wheel([binary_file], dist_dir)
    verify_source([binary_file, "MANIFEST.in"], dist_dir)


def test_only_binary__setup_output(only_binary, reset_sys_argv):

    package_dir, binary_file = only_binary
    sys.argv = ["py-build", "-sm"]
    build()
    with open(os.path.join(package_dir, "setup.py")) as opensetup:
        setup_contents = opensetup.read()

    assert 'data_files=' in setup_contents
    assert "['{}'])],".format(binary_file) in setup_contents

    with open(os.path.join(package_dir, "pypackage.meta")) as openmeta:
        meta_contents = openmeta.read()

    expected_banner = "# pypackage.meta generated by `py-build -sm` at "
    assert expected_banner in meta_contents.splitlines()[0]


if __name__ == "__main__":
    pytest.main(["-rx", "-v", "--pdb", __file__])
