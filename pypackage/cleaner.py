"""Functions related to cleaning generated/created files from building."""


import os
import io

from .constants import INPUT


def generated_setup(file_path):
    """Determine if the seutp.py is one we've generated.

    Args:
        file_path: full file path to a setup.py

    Returns:
        True if we've made the setup.py
    """

    trigger = """This file was autogenerated by pypackage. To make changes, you
should edit the pypackage.meta rather than this setup.py."""
    with io.open(file_path, "r", encoding="utf-8") as opensetup:
        return trigger in opensetup.read()


def _generated_files():
    """Finds all generated files in the current working directory.

    Returns:
        list of full file paths
    """

    generated = []
    roots = []
    for root, directories, files in os.walk(os.curdir):
        if root.startswith(("./.tox", "./.eggs", "./venv", "./.venv")):
            continue

        if root.startswith(("./build", "./dist")) \
           or "__pycache__" in root \
           or root.endswith(".egg-info"):
            roots.append(root)

        for file_ in files:
            file_path = os.path.join(root, file_)
            if root.startswith(("./build", "./dist")) \
               or "__pycache__" in root \
               or root.endswith(".egg-info") \
               or file_.endswith(".pyc") \
               or (file_ == "setup.py" and generated_setup(file_path)):
                generated.append(file_path)

    return generated, sorted(roots, reverse=True)


def clean_all(prompt=True):
    """Cleans all generated files.

    Args:
        prompt: boolean to prompt the user to confirm before deleting
    """

    to_delete, roots = _generated_files()
    if prompt:
        print("py-clean will remove the following:\n{}".format(
            "\n".join(to_delete)
        ))
        while True:
            try:
                from_user = INPUT("Are you sure? [y/N] ")
            except KeyboardInterrupt:
                raise SystemExit("Cancelled")
            if from_user.lower().startswith("y"):
                break
            elif from_user.lower().startswith("n"):
                raise SystemExit

    for filepath in to_delete:
        os.unlink(filepath)

    for root in roots:
        os.rmdir(root)
