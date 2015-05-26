"""Functions and helpers for configuring a config.Config object."""


from __future__ import print_function

import ast
import sys
from pprint import pformat

from .constants import INPUT


def ask_for_value(key):
    """Asks the user for the value of `key`, a key in the config.

    Args:
        key, string config key to query for

    Returns:
        string value from user input, or None on cancel
    """

    user_return = ""
    try:
        user_return = INPUT("Please enter the value for {}: ".format(key))
    except KeyboardInterrupt:
        print("")
        raise SystemExit("Cancelled on user request")
    return user_return or None


def handle_classifiers(config):  # pragma: no cover
    """If -c/--classifiers is used on the command line, enters a curses screen.

    Note: doesn't work on non-POSIX compliant operating systems

    Args:
        config: config object, may have classifiers set on it
    """

    try:
        from .classified import choose_classifiers
    except Exception as error:
        print(error, file=sys.stderr)
        print("Could not load classifiers selector", file=sys.stderr)
    else:
        return choose_classifiers(config)


def set_value_in_config(key, config, keys):
    """Sets a value on config by asking the user for it.

    Args::

        key: string key to ask for
        config: pypackage.config.Config object to add the attribute to
        keys: the key list with type declarations for this key

    Returns:
        None, might add an attribute to config though
    """

    if key == "classifiers":
        user_val = handle_classifiers(config)
    else:
        user_val = ask_for_value(key)

    try:
        user_val = coerce_to_expected(user_val, key, keys[key])
    except Exception as error:
        print(error, file=sys.stderr)
        return set_value_in_config(key, config, keys)

    if user_val:
        setattr(config, key, user_val)

        try:
            config._verify()
        except Exception as error:
            print(error, file=sys.stderr)
            print("{} as {} failed to verify. should be {}".format(
                key, getattr(config, key), keys[key].__name__
            ), file=sys.stderr)
            delattr(config, key)  # unset the failed to verify value
            return set_value_in_config(key, config, keys)
        else:
            print("{} set to: {}".format(key, pformat(getattr(config, key))))


def coerce_to_expected(value, key, type_):
    """Applies some simple logic to coerce value into the expected type.

    Args::

        value: the string returned from the user input
        key: the key name in config we're parsing
        type_: the type declaration for this key value
    """

    if not value:
        return value
    elif ("require" in key and "extras" not in key) or type_ is list:
        return coerce_to_list(value)
    elif isinstance(type_, dict):
        return ast.literal_eval(value)  # oh god, the humanity
    elif type_ is bool:
        try:
            return bool(ast.literal_eval(value))
        except ValueError:
            return bool(value)  # malformed strings get you here, will be True
    elif not isinstance(value, type_):
        return type_(value)
    else:
        return value


def coerce_to_list(value):
    """Splits a value into a list, or wraps value in a list.

    Returns:
        value, as a sorted list
    """

    if isinstance(value, list):
        return sorted(value)
    for split_char in (",", ";", ":", "|", " "):
        if split_char in value:
            return sorted([val.strip() for val in value.split(split_char)])
    return [value]


def standard_attributes(config, options):
    """Builds the list of attributes to query for in the standard category.

    Args:
        config: config object to use
    """

    all_in_this_cat = list(config._KEYS.keys())[:17]

    if options.re_config:
        return all_in_this_cat

    unconfigured = []
    for key in all_in_this_cat:
        if (key == "classifiers" and options.re_classify) or \
                not hasattr(config, key):
            unconfigured.append(key)

    return unconfigured


def feature_attributes(config, options):
    """Builds a list of unconfigured feature attributes in config."""

    all_in_this_cat = list(config._PYPACKAGE_KEYS.keys())

    if options.re_config:
        return all_in_this_cat

    unconfigured = []
    for key in all_in_this_cat:
        if (key == "runner_args" and not config._configured_runner_args) or \
                not hasattr(config, key):
            unconfigured.append(key)

    return unconfigured


def extended_attributes(config, options):
    """Builds a list of unconfigured extended attributes in config."""

    all_in_this_cat = list(config._KEYS.keys())[17:]

    if options.re_config:
        return all_in_this_cat

    unconfigured = []
    for key in all_in_this_cat:
        if not hasattr(config, key):
            unconfigured.append(key)

    return unconfigured


def run_interactive_setup(config, options):
    """Interactively fills in attributes of config.

    Args:
        config: pypackage.config.Config object

    Returns:
        config object, probably with more attributes
    """

    if options.re_config:
        print("Reconfiguring{}...".format(
            " {}".format(config.name) if hasattr(config, "name") else ""
        ))
    else:
        print("Starting interactive build{}...".format(
            " for {}".format(config.name) if hasattr(config, "name") else ""
        ))

    def centered(text, size=40, char="~"):
        return text.center(size, char)

    print(centered(" Standard Attributes "))
    for key in standard_attributes(config, options):
        set_value_in_config(key, config, config._KEYS)

    print(centered(" Pypackage Features "))
    for key in feature_attributes(config, options):
        set_value_in_config(key, config, config._PYPACKAGE_KEYS)

    if options.extended:
        print(centered(" Extended Attributes "))
        for key in extended_attributes(config, options):
            set_value_in_config(key, config, config._KEYS)

    return config
