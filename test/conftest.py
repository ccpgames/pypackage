"""Common fixtures for testing pypackage."""


import os
import sys
import pytest
import random
import shutil
from collections import defaultdict


class TestModule(object):
    """Static object to track the testing module name."""

    @staticmethod
    def full_path():
        name = TestModule.name()
        return os.path.join(os.path.dirname(__file__), name) if name else None

    @staticmethod
    def make_new():
        count = getattr(TestModule, "_count", hex(random.randint(0, 10000)))
        TestModule._name = "pypkg_test_module_{}".format(count)
        TestModule._count = hex(int(count, 16) + 1)
        return TestModule._name

    @staticmethod
    def name():
        return getattr(TestModule, "_name", None)


@pytest.fixture
def new_module(reset_sys_argv, move_home_pypackage):
    """Creates a new module name with TestModule and its base directory."""

    TestModule.make_new()
    mod_path = TestModule.full_path()
    os.mkdir(mod_path)
    os.chdir(mod_path)
    return mod_path


@pytest.fixture
def new_package(new_module):
    """Uses new_module to create a simple python package.

    Creates an __init__.py and my_module.py with my_function in it.

    Returns:
        tuple of module full path and package full path
    """

    mod_path, mod_name = os.path.split(new_module)
    pkg_root = os.path.join(new_module, mod_name)
    os.mkdir(pkg_root)
    write_py(pkg_root, "__init__.py")
    write_py(pkg_root, "my_module.py", my_function=True)

    # we have to write either a new find_packages() line or our package(s)
    # explicitly since we're in a subfolder of something named "test"
    with open(os.path.join(new_module, "pypackage.meta"), "w") as openmeta:
        openmeta.write('{"packages": ["find_packages()"]}')

    return new_module, pkg_root


@pytest.fixture
def simple_module(request, new_module):
    """Builds up a simple python module for testing.

    Returns:
        tuple of the module's base directory full path and module name
    """

    mod_name = "my_module_{}".format(TestModule._count)
    write_py(new_module, "{}.py".format(mod_name), my_function=True)
    request.addfinalizer(module_cleanup)
    return new_module, mod_name


@pytest.fixture
def simple_package(request, new_package):
    """Builds up a simple python package for testing.

    Returns:
        full path to the base directory of the simple package
    """

    new_module, pkg_root = new_package
    request.addfinalizer(module_cleanup)
    return new_module


@pytest.fixture
def with_data(request, new_package):
    """Builds a python package which includes data files."""

    new_module, pkg_root = new_package

    data_dir = os.path.join(pkg_root, "data")
    os.mkdir(data_dir)
    write_py(data_dir, "data_1", data=True)

    request.addfinalizer(module_cleanup)
    return new_module, pkg_root


@pytest.fixture(params=("bin", "scripts"))
def with_scripts(request, new_package):
    """Builds a python package with scripts in either ./bin or ./scripts.

    Returns:
        tuple of package directory path and script directory name
    """

    new_module, pkg_root = new_package

    scripts_dir = os.path.join(new_module, request.param)
    os.mkdir(scripts_dir)
    write_py(scripts_dir, "my_script", script=True)
    os.chmod(os.path.join(scripts_dir, "my_script"), 0o755)

    request.addfinalizer(module_cleanup)
    return new_module, request.param


def module_cleanup():
    """Used to cleanup the testing module."""

    os.chdir(os.path.dirname(__file__))
    shutil.rmtree(TestModule.full_path())


def write_py(filepath, filename, my_function=False, data=False, script=False):
    """Writes filename in filepath with my_function, data, or nothing in it.

    Args::
        filepath: base directory for the file to write
        filename: name of the file to write
        my_function: boolean to write my_function or not
        data: boolean to write "random" data or not
        script: boolean to write a script or not
    """

    contents = '"""{}\'s __init__.py"""'.format(os.path.dirname(filepath))
    if my_function:
        contents = "\n".join(["", "def my_function():", "    return True", ""])
    elif data:
        contents = "randomly 4 again"
    elif script:
        pkg = os.path.basename(os.path.dirname(filepath))
        contents = "\n".join([
            "#!{}\n\n".format(sys.executable),
            "from {} import my_module\n\n".format(pkg),
            'if __name__ == "__main__":',
            "    print(my_module.my_function())\n",
        ])

    with open(os.path.join(filepath, filename), "w") as openpy:
        openpy.write(contents)


@pytest.fixture
def reset_sys_argv(request, scope="function", autouse=True):
    """Automatically clears sys.argv before and after each test."""

    sys._argv = sys.argv
    sys.argv = ["pypackage-tests"]
    request.addfinalizer(sys_argv_reset)


def sys_argv_reset():
    """Reset function for sys.argv called at the end of each test case."""

    sys.argv = sys._argv
    del sys._argv


@pytest.fixture
def move_home_pypackage(request, scope="module", autouse=True):
    """Moves your $HOME/.pypackage file if it exists for the test session."""

    site_file = os.path.join(os.path.expanduser("~"), ".pypackage")
    tildes = 1
    while os.path.isfile("{}{}".format(site_file, "~" * tildes)):
        tildes += 1
    try:
        shutil.move(site_file, "{}{}".format(site_file, "~" * tildes))
    except Exception as error:
        if error.errno == 2:
            request.addfinalizer(nuke_home_pypackage)
        else:
            raise
    else:
        request.addfinalizer(move_home_pypackage_back)
    return site_file


def move_home_pypackage_back():
    """Returns your $HOME/.pypackage file to it's rightful place."""

    backups = defaultdict(list)
    home = os.path.expanduser("~")
    for file_name in os.listdir(home):
        if ".pypackage" in file_name and file_name.endswith("~"):
            file_path = os.path.join(home, file_name)
            backups[os.stat(file_path).st_ctime].append(file_path)

    shutil.move(
        max(backups[max(backups)]),  # the longest of the lastest created
        os.path.join(home, ".pypackage"),
    )


def nuke_home_pypackage():
    """Removes the $HOME/.pypackage file after creating it."""

    try:
        os.remove(os.path.join(os.path.expanduser("~"), ".pypackage"))
    except:
        pass
