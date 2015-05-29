# coding: utf-8
"""Functions and helpers related to guessing configuration attributes."""


from __future__ import unicode_literals

import os
import re
import codecs
from collections import namedtuple
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


def latest_git_tag():
    """Returns the latest tag from git, if .git exists."""

    def git_tag_refs(file_=""):
        return os.path.join(".git", "refs", "tags", file_)

    try:
        git_tags = os.listdir(git_tag_refs())
    except OSError:
        return None

    latest_tag = {0: None}
    for tag in git_tags:
        latest_tag[os.stat(git_tag_refs(tag)).st_ctime] = tag

    return latest_tag[max(latest_tag)]


def find_in_files():
    """Look through most files to try to determine the version and author.

    Returns:
        OrderedDict with the some/all of the following keys if found::

            version, author, author_email, maintainer, maintainer_email
    """

    Guess = namedtuple("Guess", ("source", "weight", "guess"))

    versions = []
    authors = []
    emails = []
    maintainers = []
    maintainer_emails = []

    git_tag = latest_git_tag()
    if git_tag:
        versions.append(Guess("git tag", 99, git_tag))

    to_find = OrderedDict([
        ("version", versions),
        ("author", authors),
        ("email", emails),
        ("author_email", emails),
        ("maintainer", maintainers),
        ("maintainer_email", maintainer_emails),
    ])

    file_weights = {  # additional to the pattern weights
        "__init__.py": 100,
        "__version__.py": 125,
        "version.py": 75,
    }

    for root, directories, files in os.walk(os.curdir):

        if _ignored(root, is_file=False):
            continue

        for file_ in files:
            file_path = os.path.join(root, file_)
            # ignore large files, allows us to be faster with regex's/reading
            if os.stat(file_path).st_size > 102400:
                continue

            with open(file_path, "rb") as openfile:
                try:
                    content = codecs.decode(openfile.read(), "utf-8")
                except UnicodeDecodeError:
                    continue

            for name, guesses in to_find.items():
                for i in range(3):
                    pattern = r'^{u}{name}{u} *= *[\'"]([^\'"]*)[\'"]'.format(
                        u="_" * i,
                        name=name,
                    )

                    re_match = re.search(pattern, content, re.M)
                    if re_match:
                        match_weight = 25 * (i + 1)  # more _ == more important
                        if file_ in file_weights:
                            match_weight += file_weights[file_]

                        guess = re_match.group(1)
                        try:
                            # try to use an ascii string if possible
                            guess = str(codecs.encode(guess, "ascii").decode())
                        except UnicodeEncodeError:
                            pass

                        guesses.append(Guess(
                            "{u_}{name}{u_} from file {fname}".format(
                                u_="_" * i,
                                name=name,
                                fname=file_path,
                            ),
                            match_weight,
                            guess,
                        ))
                        break

    to_find.pop("email")  # duplicated to match either email or author_email
    return OrderedDict((name, max(guesses, key=lambda x: x.weight).guess) for
                       name, guesses in to_find.items() if guesses)


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
        "EGG-INFO",
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
        if re.match(pattern, file_or_dir, re.I):
            return True

    return False


def _guess_at_things(config):
    """Guesses at attributes of this package's setup configuration.

    Returns:
        OrderedDict of {attribute: guess}
    """

    guesses = OrderedDict(
        name=os.path.basename(os.path.realpath(os.path.curdir))
    )
    guesses.update(find_in_files())

    py_modules = python_modules()
    if py_modules:
        guesses["py_modules"] = py_modules

    scripts = []
    for potential in ("scripts", "bin"):
        root = os.path.join(os.path.abspath(os.curdir), potential)
        if os.path.isdir(root):
            for file_ in os.listdir(root):
                if os.access(os.path.join(root, file_), os.X_OK):
                    scripts.append(os.path.join(potential, file_))

    if scripts:
        guesses["scripts"] = scripts

    package_files = potential_data_files(scripts)
    if package_files:
        guesses["package_data"] = package_files

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
            "\n".join(['{} `{}` = "{}"'.format(
                index,
                attr,
                guesses[attr]
            ) for index, attr in enumerate(guesses, 1)])
        ))
        len_g = len(guesses)
        query = 'use 1-{} or "all" to ignore (enter to accept): '.format(len_g)
        from_user = True
        while from_user and any([guesses[key] for key in guesses]):
            try:
                from_user = INPUT(query)
            except (EOFError, KeyboardInterrupt):
                raise SystemExit("\nInterrupted")
            try:
                from_user = int(from_user)
                assert 1 <= from_user <= len_g  # no negatives, inside len_g
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

    for attr in guesses:
        if (not hasattr(config, attr) or options.re_probe) and guesses[attr]:
            config._metadata_exclusions.append(attr)
            if attr == "package_data":  # set the name as late as possible
                setattr(config, attr, {
                    getattr(config, "name", guesses["name"]): guesses[attr]
                })
            else:
                setattr(config, attr, guesses[attr])

    if getattr(config, "package_data", None) and \
            not getattr(config, "include_package_data", None):
        config.include_package_data = True
