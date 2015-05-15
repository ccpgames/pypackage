"""Functions and helpers related to guessing configuration attributes."""


import os
import re
from collections import OrderedDict

from .constants import INPUT


def python_modules():
    """Determine if there are python modules in the cwd.

    Returns:
        list of python modules as strings
    """

    ignored = ["setup.py", "conftest.py"]

    py_modules = []
    for file_ in os.listdir(os.path.abspath(os.curdir)):
        if file_ in ignored or not os.path.isfile(file_):
            continue

        file_name, file_ext = os.path.splitext(file_)
        if file_ext == ".py":
            py_modules.append(file_name)

    return sorted(py_modules)


def potential_data_files(scripts):
    """Determine if there are any potential data files down from cwd.

    Tries to ignore normal things that would pop up you'd like not to include.

    Args:
        scripts: list of known script exectuables

    Returns:
        list of files as relative paths down from cwd
    """

    potential_files = []

    for root, directories, files in os.walk(os.curdir):
        if _ignored(root, is_file=False):
            continue

        for file_ in files:
            if not _ignored(file_):
                relative_path = os.path.join(root, file_)
                while relative_path[0] in (os.curdir, os.path.sep):
                    relative_path = relative_path[1:]
                if relative_path not in scripts:
                    potential_files.append(relative_path)

    return potential_files


def _ignored(file_or_dir, is_file=True, _recurse=False):
    """Return a boolean of if this file or dir is ignored.

    Args::

        file_or_dir: string file or directory name
        is_file: boolean of if this is a file
    """

    ignored_files = [
        "MANIFEST.in",
        "setup.cfg",
        ".travis.yml",
        ".coverage",
        ".coveragerc",
        ".gitignore",
        "tox.ini",
        "conftest.py",
        "pypackage.meta",
    ]

    ignored_file_patterns = [
        r".*\.pyc$",
        r".*\.py$",  # These will be found as part of a package
    ]

    ignored_dirs = [
        "__pycache__",
        "build",
        "dist",
        ".git",
        ".svn",
        ".eggs",
    ]

    ignored_dir_patterns = [
        r"docs?",
        r"examples?",
        r".*\.egg$",
        r".*\.egg-info$",
        r"tests?",
    ]

    if not is_file:
        return any([_ignored(part, _recurse=True) for
                    part in file_or_dir.split(os.path.sep)])

    file_or_dir = os.path.basename(file_or_dir)
    ignored = ignored_dirs if _recurse else ignored_files

    if file_or_dir in ignored:
        return True

    patterns = ignored_dir_patterns if _recurse else ignored_file_patterns
    for pattern in patterns:
        if re.match(pattern, file_or_dir):
            return True

    return False


def _guess_at_things(config):
    """Guesses at attributes of this package's setup configuration.

    Returns:
        OrderedDict of {attribute: guess}
    """

    guesses = OrderedDict([
        ("name", os.path.basename(os.path.realpath(os.path.curdir))),
        ("py_modules", python_modules()),
    ])

    scripts = []
    for potential in ["scripts", "bin"]:
        root = os.path.join(os.path.abspath(os.curdir), potential)
        if os.path.isdir(root):
            for file_ in os.listdir(root):
                if os.access(os.path.join(root, file_), os.X_OK):
                    scripts.append(os.path.join(potential, file_))

    guesses["scripts"] = scripts

    package_files = potential_data_files(scripts)
    if package_files:
        guesses["package_data"] = {
            getattr(config, "name", guesses["name"]): package_files
        }

    return guesses


def perform_guesswork(config, options):
    """Look for missing attributes and take a guess at them.

    Confirm with the user that the guesses are correct after making them if
    they are in interactive mode, otherwise just display them as found.

    Args::

        config: config object to inspect/set attrributes on
        options: options object for cmd line flags
    """

    guesses = _guess_at_things(config)

    if options.interactive:
        # confirm guesses...
        print((
            "pypackage has guessed the following attributes:\n{}\n"
            "would you like to disregard any of the above guesses?"
        ).format(
            "\n".join(["{} `{}` = {!r:}".format(
                index,
                attr,
                guesses[attr]
            ) for index, attr in enumerate(guesses, 1)])
        ))
        len_g = len(guesses)
        query = 'use 1-{} or "all" to ignore (enter to accept): '.format(len_g)
        from_user = True
        while from_user and any([guesses[key] for key in guesses]):
            from_user = INPUT(query)
            try:
                from_user = int(from_user)
                assert 1 < from_user <= len_g  # no negatives, inside len_g
            except:
                if str(from_user).strip().lower() == "all":
                    print("ignoring all guesses")
                    guesses = {}
                elif from_user:
                    print("{} is invalid.".format(from_user))
            else:
                # this is a hack, and the reason guess is an OrderedDict
                from_user = list(guesses.keys())[from_user - 1]
                guesses[from_user] = None
                print("{} will not be guessed".format(from_user))

    for atr in ("name", "scripts", "py_modules", "package_data"):
        if (not hasattr(config, atr) or options.re_probe) and guesses.get(atr):
            setattr(config, atr, guesses[atr])

    if getattr(config, "package_data", None) and \
            not getattr(config, "include_package_data", None):
        config.include_package_data = True
