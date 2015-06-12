"""Reads static configuration metadata and creates a Python object."""


from __future__ import print_function

import io
import os
import re
import copy
import json
import nose
import yaml
import pytest
import logging
import unittest
from pprint import pformat
from collections import OrderedDict
from setuptools import find_packages

from .runner import TestRunner
from .runner import NOSE_TEMPLATE
from .runner import PYTEST_TEMPLATE
from .runner import UNITTEST_TEMPLATE
from .constants import META_NAME
from .constants import STRING_TYPE


class UNDEF(object):
    """Used to differentiate None/0/False from an option not being defined."""

    pass


class SetOnce(list):
    """Subclass list to have append only append if the value is not in list."""
    def append(self, value):
        if value not in self:
            super(SetOnce, self).append(value)


class Config(object):
    """Config object. Attributes are passed as kwargs."""

    _KEYS = OrderedDict([  # all available configuration keys: value type
        ("name", str),
        ("version", str),
        ("description", str),
        ("long_description", str),
        ("author", str),
        ("author_email", str),
        ("maintainer", str),
        ("maintainer_email", str),
        ("url", str),
        ("download_url", str),
        ("packages", list),
        ("py_modules", list),
        ("scripts", list),
        ("entry_points", {str: list}),
        ("install_requires", (str, list)),
        ("tests_require", (str, list)),
        ("classifiers", list),
        # ~~ separation of standard/extended here ~~
        ("ext_modules", list),
        ("keywords", list),
        ("platforms", list),
        ("cmdclass", {str: object}),
        ("data_files", (list,)),
        ("package_dir", {str: str}),
        ("build_requires", (str, list)),
        ("setup_requires", (str, list)),
        ("extras_require", {str: list}),
        ("include_package_data", bool),
        ("exclude_package_data", {str: list}),
        ("package_data", {str: list}),
        ("zip_safe", bool),
        ("dependency_links", list),
        ("namespace_packages", list),
        ("test_suite", str),
        ("test_loader", str),
        ("eager_resources", list),
        ("use_2to3", bool),
        ("convert_2to3_doctests", list),
        ("use_2to3_fixtures", list),
    ])
    # our distinct keys, these do not get passed to setuptools/distutils
    _PYPACKAGE_KEYS = OrderedDict([
        ("test_runner", str),
        ("tests_dir", str),     # no function required for these two, they're
        ("runner_args", list),  # only used in the enable_test_runner function
    ])

    def __init__(self, **kwargs):
        """Builds a Config object, fills in options passed as kwargs."""

        config_as_dict = {key: UNDEF() for key in Config._KEYS}
        config_as_dict.update({key: UNDEF() for key in Config._PYPACKAGE_KEYS})
        self._defaults = site_defaults()
        config_as_dict.update(self._defaults)
        config_as_dict.update(kwargs)

        extras = {}
        for key, value in config_as_dict.items():
            if not isinstance(value, UNDEF):
                if re.match(".*_requires?$", key) and key not in Config._KEYS:
                    extras[key.rpartition("_")[0]] = value
                else:
                    setattr(self, key, value)

        if extras:
            if hasattr(self, "extras_require"):
                self.extras_require.update(extras)
            else:
                self.extras_require = extras

        # duplicate in some values
        duplicate_values = [
            ("description", "long_description"),
            ("author", "maintainer"),
            ("author_email", "maintainer_email"),
        ]
        for orig, alias in duplicate_values:
            if hasattr(self, orig):
                setattr(self, alias, getattr(self, alias, getattr(self, orig)))
                if getattr(self, orig) == getattr(self, alias):
                    self._defaults[alias] = getattr(self, alias)

        # _verify will toggle these if set
        self._configured_runner_args = False
        self._configured_tests_require = False
        self._long_read = ""  # used in direct setuptools interactions
        self._long_read_in_setup = ""  # used in writing the setup.py

        # filled in during guessing phase
        self._metadata_exclusions = SetOnce()

        # perform init-time type validation and runs feature functions
        self._verify()

    @property
    def _as_kwargs(self):
        """Builds a dict suitable for use with setuptools.setup directly."""

        kwargs = OrderedDict()

        for key in Config._KEYS:
            if hasattr(self, key):
                if key == "packages":
                    for package in self.packages:
                        if package.startswith("find_packages(") and \
                                ";" not in package and "." not in package:
                            # no ;'s or .'s here to reduce attack surface
                            try:
                                found_packages = eval(package)
                            except:
                                continue
                            else:
                                kwargs[key] = found_packages
                                break
                    else:
                        kwargs[key] = self.packages
                elif key == "long_description":
                    kwargs[key] = self._long_read or self.long_description
                else:
                    kwargs[key] = getattr(self, key)

        if "packages" not in kwargs:
            packages = find_packages(exclude=["test", "tests"])
            if packages:
                kwargs["packages"] = packages

        return kwargs

    @property
    def _metadata(self):
        """Metadata unique to this config."""

        metadata = OrderedDict([(k, v) for k, v in self._as_kwargs.items()
                                if k not in self._defaults])
        # remove the cmdclass key and tests_require if not set by the user
        metadata.pop("cmdclass", None)
        if not self._configured_tests_require:
            metadata.pop("tests_require", None)

        # remove anything that's been guessed
        for key in self._metadata_exclusions:
            metadata.pop(key, None)

        # reset long_description back to the filename
        if self._long_read:
            metadata["long_description"] = self.long_description

        # add in feature keys that have been set
        for attr in Config._PYPACKAGE_KEYS:
            if hasattr(self, attr):
                if attr != "runner_args" or self._configured_runner_args:
                    metadata[attr] = getattr(self, attr)

        return metadata

    def __str__(self):
        """Creates a string representation of self, resulting in a setup.py."""

        packages_str, find_needed = self._packages_string()
        cmdclass = self._cmdclass_string()
        long_descr_str = self._long_description_string()

        altered_keys = ("packages", "long_description", "cmdclass")
        altered_strs = (packages_str, long_descr_str, cmdclass)

        imports = ["from setuptools import setup"]
        if find_needed:
            imports.append("from setuptools import find_packages")
        if self._long_read_in_setup:
            imports.insert(0, "import io")

        return "\n".join([
            '"""{}\'s setup.py.\n'.format(
                getattr(self, "name", "None").title()
            ),
            "This file was autogenerated by pypackage. To make changes, you",
            "should edit the {} rather than this setup.py.".format(META_NAME),
            '"""\n\n',
            "\n".join(imports),
            self._test_runner_string() or "\n",
            "{}setup(".format(self._long_read_in_setup),
            "\n".join([
                "    {}={},".format(key, _multiline(val)) for key, val in
                self._as_kwargs.items() if key not in altered_keys
            ]),
            "\n".join(
                ["    {},".format(altered_str) for altered_str in altered_strs
                    if altered_str]
            ) or "",
            ")",
        ])

    def _long_description_string(self):
        """Builds a string for long_description (+file read) in setup.py."""

        if not hasattr(self, "long_description"):
            return

        if self._long_read_in_setup:
            return "long_description=long_description"
        else:
            return "long_description={!r:}".format(self.long_description)

    def _test_runner_string(self):
        """Builds a string from the test_runner template, if in use."""

        if not hasattr(self, "test_runner"):
            return

        if self.test_runner == "unittest":  # extra formatting
            return UNITTEST_TEMPLATE.format(
                self=self,
                tests_dir=getattr(self, "tests_dir", "."),
            )
        elif self.test_runner == "nose":
            return NOSE_TEMPLATE.format(self=self)
        else:
            return PYTEST_TEMPLATE.format(self=self)

    def _packages_string(self):
        """Builds a string for `packages=` in the setup.py.

        Returns:
            tuple of a packages string and boolean of requiring find_packages
        """

        # defaults
        excludes = ["test", "tests"]
        package_str = "find_packages(exclude={!r:})".format(excludes)
        find_required = True

        if hasattr(self, "packages"):
            for package in self.packages:
                if "find_packages(" in package:
                    # user supplied a find_packages() string
                    package_str = package
                    break
            else:
                # user supplied packages list
                package_str = repr(self.packages)
                find_required = False

        return "packages={}".format(package_str), find_required

    def _cmdclass_string(self):
        """Builds a string for `cmdclass=` in the setup.py."""

        cmdclass = getattr(self, "cmdclass", {})
        as_string = copy.deepcopy(cmdclass)
        if "test" in as_string:
            as_string["test"] = "PyPackageTest"  # name in template

        if as_string:
            return "cmdclass={{{}}}".format(", ".join(  # repr the keys only
                "{!r:}: {}".format(k, v) for k, v in as_string.items()
            ))

    def __repr__(self):
        return "<{name}.{cls} object at {id}, {attributes}>".format(
            name=__name__,
            cls=self.__class__.__name__,
            id=hex(id(self)),
            attributes=", ".join(
                ["{attr}: '{{self.{attr}}}'".format(attr=attr)
                 for attr in dir(self) if not attr.startswith("_")]
            ).format(self=self),
        )

    def _enable_long_description_read(self):
        """Sets up the automatic read feature of long_description.

        Returns:
            None, modifies attributes of self
        """

        if self._long_read or not hasattr(self, "long_description"):
            return

        try:
            if os.path.isfile(self.long_description):
                with io.open(self.long_description, encoding="utf-8") as descr:
                    self._long_read = descr.read()
                self._long_read_in_setup = (
                    'with io.open("{}", encoding="utf-8") as opendescr:\n'
                    "    long_description=opendescr.read()\n\n\n"
                ).format(
                    self.long_description
                )
            else:
                return
        except:
            return

    def _enable_test_runner(self):
        """Sets up the preferred testing suite.

        Returns:
            None, modifies attributes of self
        """

        if not hasattr(self, "test_runner"):
            return

        test_runner = self.test_runner.lower()
        if test_runner == "pytest":
            self._enable_pytest()
        elif test_runner.startswith("nose"):  # allow nosetests... etc
            self.test_runner = "nose"  # exact name for importing though
            self._enable_nosetest()
        else:
            self.test_runner = "unittest"
            self._enable_unittest()

        TestRunner.pypackage(self)  # XXX after runner_args are set
        self.cmdclass = {"test": TestRunner}

    def _enable_nosetest(self):
        """Do nosetest specific logic to enable it as a test runner."""

        default_args = ["-v", "-d", "--with-coverage", "--cov-report",
                        "term-missing", "--cov"]

        self._runner = nose

        # grab the user's tests_require, make sure nose is in there
        self.tests_require = getattr(self, "tests_require", None)
        if self.tests_require is None:
            self.tests_require = ["nose"]
        else:
            self._configured_tests_require = self.tests_require not in (
                ["nose"], ["nose", "nose-cov"])
            if "nose" not in self.tests_require:
                self.tests_require.append("nose")

        # configure the default or user supplied runner arguments
        arg_len = 1 + (int(hasattr(self, "tests_dir")) * 2)  # *2 b/c -w flag
        self.runner_args = getattr(self, "runner_args", None)
        if self.runner_args is None:
            self.runner_args = default_args[:2]
            if hasattr(self, "name"):
                self.runner_args.extend(default_args[2:] + [self.name])
                if "nose-cov" not in self.tests_require:
                    self.tests_require.append("nose-cov")
        elif len(self.runner_args) == len(default_args) + arg_len and \
                self.runner_args[:-arg_len] == default_args:
            # refresh runner_args in case our name has changed for coverage
            self.runner_args = default_args + [getattr(self, "name", "")]
            if "nose-cov" not in self.tests_require:
                self.tests_require.append("nose-cov")
        else:
            self._configured_runner_args = True  # include them in metadata

        # use -w to specify NOSEWHERE, or let nose find the tests itself
        if hasattr(self, "tests_dir"):
            self.runner_args.extend(["-w", self.tests_dir])

    def _enable_unittest(self):
        """Do unittest specific logic to enable it as a test runner."""

        self._runner = unittest
        self.runner_args = getattr(self, "runner_args", None)
        if self.runner_args is None:
            self.runner_args = []
        else:
            self._configured_runner_args = True

    def _enable_pytest(self):
        """Do pytest specific logic to enable it as a test runner."""

        default_args = ["-v", "-rx", "--cov-report", "term-missing", "--cov"]

        self._runner = pytest

        # grab the user's tests_require, make sure pytest is in there
        self.tests_require = getattr(self, "tests_require", None)
        if self.tests_require is None:
            self.tests_require = ["pytest"]
        else:
            self._configured_tests_require = self.tests_require not in (
                ["pytest"], ["pytest", "pytest-cov"])
            if "pytest" not in self.tests_require:
                self.tests_require.append("pytest")

        # configure the default or user supplied runner arguments
        arg_len = 1 + int(hasattr(self, "tests_dir"))  # name + dir if supplied
        self.runner_args = getattr(self, "runner_args", None)
        if self.runner_args is None:
            self.runner_args = default_args[:2]
            if hasattr(self, "name"):
                self.runner_args.extend(default_args[2:] + [self.name])
                if "pytest-cov" not in self.tests_require:
                    self.tests_require.append("pytest-cov")
        elif len(self.runner_args) == len(default_args) + arg_len and \
                self.runner_args[:-arg_len] == default_args:
            # refresh runner_args in case our name has changed for coverage
            self.runner_args = default_args + [getattr(self, "name", "")]
            if "pytest-cov" not in self.tests_require:
                self.tests_require.append("pytest-cov")
        else:
            self._configured_runner_args = True  # include them in metadata

        # tack the tests dir on the end, or let pytest find them
        if hasattr(self, "tests_dir"):
            self.runner_args.append(self.tests_dir)

    def _verify(self):
        """Ensures self attributes conform to their type declarations."""

        self._enable_test_runner()
        self._enable_long_description_read()

        for key, type_ in list(Config._KEYS.items()) + list(
                Config._PYPACKAGE_KEYS.items()):
            if hasattr(self, key):
                self._verify_key(key, type_)

    def _verify_key(self, key, type_):
        """Verify that key is of type type_.

        Raises:
            TypeError if they key cannot be coerced into type_
        """

        if isinstance(type_, dict) and isinstance(getattr(self, key), dict):
            setattr(self, key, ensure_dict(getattr(self, key), type_))
        elif isinstance(type_, dict):
            raise TypeError("{} should be a dict, not {}!".format(
                key,
                type(getattr(self, key)).__name__,
            ))
        elif type_ is list and isinstance(getattr(self, key), list):
            setattr(self, key, ensure_list(getattr(self, key)))
        elif type_ is list:
            setattr(self, key, [getattr(self, key)])
        elif not isinstance(getattr(self, key), type_):
            if isinstance(type_, tuple):  # multiple acceptable values
                for type__ in type_:
                    if type__ is list:
                        setattr(self, key, [getattr(self, key)])
                        break
                    else:
                        try:
                            setattr(self, key, type__(getattr(self, key)))
                            break
                        except:
                            pass
                else:
                    raise TypeError("{} should be a {} or {}, not {}!".format(
                        key,
                        ", ".join([t.__name__ for t in type_[:-1]]),
                        type_[-1].__name__,
                        type(getattr(self, key)).__name__,
                    ))
            else:
                try:
                    setattr(self, key, type_(getattr(self, key)))
                except:
                    raise TypeError("{} should be a {}, not {}!".format(
                        key, type_.__name__, type(getattr(self, key)).__name__,
                    ))


def _multiline(value, indent=4):
    """Return value as a multiline (pretty) string, with indent."""

    val = pformat(value)
    if "\n" in val:
        value_as_lines = val.splitlines()

        indented = [
            "{}".format(value_as_lines[0][0]),  # rip the leading bracket
            "{}{}".format(" " * (indent * 2), value_as_lines[0][1:].strip()),
        ]
        for line in value_as_lines[1:-1]:
            indented.append("{}{}".format(" " * (indent * 2), line.strip()))
        indented.extend([
            "{}{}".format(" " * (indent * 2), value_as_lines[-1][:-1].strip()),
            "{}{}".format(" " * indent, value_as_lines[-1][-1]),
        ])
        val = "\n".join(indented)
    return val


def ensure_list(list_to_verify):
    """Ensures that all items in the list are of string type.

    Also guarentees that all items in the list are unique. Maintains order.
    """

    string_list = []

    def string_list_append(item):
        if item not in string_list:
            string_list.append(item)

    for item in list_to_verify:
        if isinstance(item, STRING_TYPE):
            string_list_append(item)
        else:
            string_list_append(str(item))

    return string_list


def ensure_dict(dict_to_verify, dict_types):
    """Goes through dict_to_verify and tries to coerce into dict_types.

    Args::

        dict_to_verify: a dict with keys and values to verify
        dict_types: a dict with a single key/value pair of the expected types

    Returns:
        a new dictionary, coerced into the correct types
    """

    key_type = list(dict_types.keys())[0]
    value_type = list(dict_types.values())[0]
    return_dict = {}
    for key, value in dict_to_verify.items():
        if not isinstance(key, key_type):
            key = key_type(key)  # this will raise on error...
        if not isinstance(value, value_type):
            if value_type is list and isinstance(key, STRING_TYPE):
                value = [value]  # auto list single string values
            else:
                value = value_type(value)  # this will also raise on error...
        return_dict[key] = value
    return return_dict


def site_defaults():
    """Look for site default metadata to mixin onto any missing values."""

    filename = os.path.join(os.path.expanduser("~"), ".pypackage")
    if os.path.isfile(filename):
        return json_maybe_commented(filename) or {}
    else:
        logging.debug("Site defaults requested but not found at %s", filename)
        return {}


def get_config(path=None):
    """Looks in path or os.cwd for a static metadata file and builds a config.

    Args:
        path: optional string path to search inside, or None for cwd

    Returns:
        Config object to build/install with or None on error
    """

    if path is None:
        path = os.path.abspath(os.path.curdir)

    pyjson = os.path.join(path, META_NAME)
    if os.path.isfile(pyjson):
        return Config(**json_maybe_commented(pyjson))
    else:
        logging.info("Using site defaults, no %s found in %s", META_NAME, path)
        return Config()


def reduce_json_unicode(json_obj):
    """Stupidly dumps JSON into YAML to remove what unicode it can."""

    return yaml.safe_load(json.dumps(json_obj))


def json_maybe_commented(filename, remove_comments=False):
    """Tries twice to load the filename as JSON.

    The second time, if needed, it will remove lines starting with `#`.
    """

    if remove_comments:
        cleaned_lines = []
        with open(filename, "r") as openfile:
            for line in openfile:
                if not re.match("\s*#", line):  # leading whitespace then #
                    cleaned_lines.append(line)
        try:
            return reduce_json_unicode(json.loads("".join(cleaned_lines)))
        except Exception as error:
            logging.error("Error reading json from %s: %r", filename, error)
            return {}
    else:
        try:
            with open(filename, "r") as openfile:
                return reduce_json_unicode(json.loads(openfile.read()))
        except Exception as error:
            logging.debug("Commented JSON? Recursing because: %r", error)
            return json_maybe_commented(filename, remove_comments=True)
