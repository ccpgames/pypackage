"""Tests for pypackages' config object and helper functions."""


import json
import mock
import pytest
import tempfile

from pypackage import config
from pypackage.config import Config


def test_requires_into_extras():
    """Any x_requires param should be converted to an extras_require param."""

    conf = Config(foo_requires=["bar"], bar_requires=["foo"],
                  baz_require=["foobar"])
    assert conf.extras_require == {
        "foo": ["bar"],
        "bar": ["foo"],
        "baz": ["foobar"],
    }


def test_malformed_packages_fallback():
    """Invalid values using find_packages should fallback to their string."""

    garbage = "find_packages(!@!^%&)%*_!()$*!*^!%&*(!)$@_!*)"
    conf = Config(packages=[garbage])
    assert conf.packages == [garbage]
    assert conf._as_kwargs.get("packages") == [garbage]
    assert conf._packages_string() == ("packages={}".format(garbage), True)


def test_supplied_packages():
    """Ensure the user can provide the packages list."""

    conf = Config(packages="my_package")
    assert conf._packages_string() == ("packages=['my_package']", False)


@pytest.mark.parametrize("runner", ("unittest", "nose", "pytest"))
def test_runner_args_only_when_set(runner):
    """runner_args should only be in the metadata when they're non-default."""

    conf = Config(test_runner=runner)
    assert "runner_args" not in conf._metadata

    conf2 = Config(test_runner=runner, runner_args=["-vv", "--pdb"])
    assert conf2._metadata.get("runner_args") == ["-vv", "--pdb"]


@pytest.mark.parametrize("runner", ("nose", "pytest"))
def test_runner_args_with_tests_dir(runner):
    """If pytest or nose is used, the tests dir should be the last runner arg.

    When unittest is used, the tests_dir is injected into UNITTEST_TEMPLATE.
    """

    conf = Config(test_runner=runner, tests_dir="somewhere")
    assert conf.runner_args[-1] == "somewhere"


def test_runner_string__unittest():
    """Ensure the correct template and formatting is used for unittest."""

    conf = Config(
        test_runner="unittest is the default when provided nonsense",
        tests_dir="my_non_std_tests",
    )
    template_str = conf._test_runner_string()

    assert "import unittest" in template_str
    assert "my_non_std_tests" in template_str


@pytest.mark.parametrize("runner", ("nose", "pytest"))
def test_runner_string(runner):
    """Ensure the correct template is used for nose and pytest."""

    conf = Config(test_runner=runner)
    template_str = conf._test_runner_string()
    assert "import {}".format(runner) in template_str


def test_cmdclass_string():
    """Ensure the cmdclass string outputting is correct."""

    conf = Config(cmdclass={"foo": "MyFooClass", "test": "gets overridden"})
    cmdcls_str = conf._cmdclass_string()
    assert cmdcls_str.startswith("cmdclass={")
    assert "'foo': MyFooClass" in cmdcls_str
    assert "'test': PyPackageTest" in cmdcls_str


def test_repr():
    """Config should have some sort of repr that's not a setup.py."""

    conf = Config()
    assert "Config object at {}".format(hex(id(conf))) in repr(conf)


@pytest.mark.parametrize("runner", ("nose", "pytest"))
def test_additional_tests_require(runner):
    """If there are provided tests_require, they should be mixed in."""

    # we get runner-cov here becuase we provide a name
    conf = Config(name="test", test_runner=runner, tests_require=["my_thing"])
    assert conf.tests_require == ["my_thing", runner, "{}-cov".format(runner)]
    assert conf.runner_args[-1] == "test"
    # change our name here, we should get our new name in runner_args
    conf.name = "changed"
    # also we can reset tests_require and they should re-populate
    conf.tests_require = ["my_thing"]
    conf._verify()
    assert conf.runner_args[-1] == "changed"


def test_verify_key__dict_failure():
    """Do not try to coerce something that should be a dict into one."""

    conf = Config()
    conf.foo = "not a dict"
    with pytest.raises(TypeError) as error:
        conf._verify_key("foo", {})
    assert error.value.args[0] == "foo should be a dict, not str!"


def test_verify_key__list_object():
    """If an attribute should be a list, it should be listed."""

    conf = Config()
    conf.foo = "not a list"
    conf._verify_key("foo", list)
    assert conf.foo == ["not a list"]


def test_verify_key__multiple__allowed():
    """There are some keys where multiple types are allowed."""

    conf = Config()
    conf.foo = 3.14
    conf._verify_key("foo", (list, str))
    assert conf.foo == [3.14]

    conf.foo = 3.14
    conf._verify_key("foo", (str, list))  # assert order matters
    assert conf.foo == "3.14"


def test_verify_key__multiple__fallthrough():
    """If the first coerce fails, try the second."""

    conf = Config()
    conf.bar = mock.MagicMock(spec=False)
    conf.bar.__float__ = mock.Mock(side_effect=ValueError)
    conf.bar.__str__ = mock.Mock(return_value="mock str")
    conf._verify_key("bar", (float, str))
    assert conf.bar == "mock str"


def test_verify_key__multiple__failure():
    """When unable to coerce to any type, raise TypeError."""

    conf = Config()
    conf.foo = mock.MagicMock(spec=False)
    conf.foo.__float__ = mock.Mock(side_effect=ValueError)
    conf.foo.__str__ = mock.Mock(side_effect=ValueError)
    with pytest.raises(TypeError) as err:
        conf._verify_key("foo", (float, str))
    assert err.value.args[0] == "foo should be a float or str, not MagicMock!"


def test_verify_key__failure_coerce():
    """Should try to coerce values into their types when not list or dict."""

    conf = Config()
    conf.foo = 3.14
    conf._verify_key("foo", str)
    assert conf.foo == "3.14"


def test_verify_key__failure():
    """If unable to coerce into the expected type, raise TypeError."""

    conf = Config()
    conf.foo = "something"
    with pytest.raises(TypeError) as error:
        conf._verify_key("foo", float)
    assert error.value.args[0] == "foo should be a float, not str!"


def test_verify_key__str_list_values():
    """If the type is list, the items inside should be strings."""

    conf = Config()
    conf.foo = ["bar", 3.14, "baz"]
    conf._verify_key("foo", list)
    assert conf.foo == ["bar", "3.14", "baz"]


def test_verify_key__dict_types():
    """If a dict is provided with types, the key/values should be coerced."""

    conf = Config()
    conf.foo = {3.14: "500.123"}
    conf._verify_key("foo", {str: float})
    assert conf.foo == {"3.14": 500.123}


def test_multiline():
    """Ensure the proper formatting for multiline pprint formats."""

    blurb = "really long string that will require multiple lines"
    blurber = lambda x: "{}-{}".format(blurb, x)
    value = [blurber(i) for i in range(5)]
    assert config._multiline(value) == """[
        'really long string that will require multiple lines-0',
        'really long string that will require multiple lines-1',
        'really long string that will require multiple lines-2',
        'really long string that will require multiple lines-3',
        'really long string that will require multiple lines-4'
    ]"""


def test_json_loading__failure():
    """Ensure the error logged and empty return value on invalid json file."""

    filename = tempfile.mktemp()
    with open(filename, "w") as openfile:
        openfile.write("# yeah comments are ok\n{but invalid json: [is not]}")

    with mock.patch.object(config.logging, "error") as patched_err_log:
        assert config.json_maybe_commented(filename) == {}

    assert patched_err_log.call_args[0][0] == "Error reading json from %s: %r"
    assert patched_err_log.call_args[0][1] == filename
    assert isinstance(patched_err_log.call_args[0][2], ValueError)
    assert patched_err_log.call_count == 1


@pytest.mark.parametrize("original, alias", [
    ("author", "maintainer"),
    ("author_email", "maintainer_email"),
    ("description", "long_description"),
])
def test_default_fillins(original, alias):
    """pypackage maps a few attributes to aliases if 1/2 is supplied."""

    conf = Config(**{original: "something"})
    assert getattr(conf, alias) == "something"


def test_site_defaults_mixin(move_home_pypackage):
    """Ensure the site defaults are mixed in if available."""

    with open(move_home_pypackage, "w") as opensite:
        opensite.write(json.dumps({"author": "you!"}))
    conf = Config()
    assert conf.author == "you!"


def test_metadata_excludes_set_once():
    """Ensure you can only add to _metadata_excludes once."""

    conf = Config()
    conf._metadata_exclusions.append("foo")
    conf._metadata_exclusions.append("foo")
    conf._metadata_exclusions.append("foo")
    conf._metadata_exclusions.append("bar")
    conf._metadata_exclusions.append("foo")
    conf._metadata_exclusions.append("bar")
    assert conf._metadata_exclusions == ["foo", "bar"]


def test_extras_require_mixin():
    """Ensure you can provide both extras_require and X_requires."""

    conf = Config(
        extras_require={"my_thing": ["foo"]},
        feature_x_requires="bar",
    )
    assert conf.extras_require == {"my_thing": ["foo"], "feature_x": ["bar"]}


def test_as_kwargs_finds_packages():
    """The _as_kwargs property should use find_packages."""

    conf = Config()
    with mock.patch.object(config, "find_packages", return_value=4) as patched:
        conf_args = conf._as_kwargs

    assert conf_args["packages"] == 4
    patched.assert_called_once_with(exclude=["test", "tests"])


def test_long_read_errors_buried(with_readme):
    """Errors when trying to read long_description file should be buried."""

    with mock.patch.object(config.io, "open", side_effect=OSError):
        conf = config.get_config(with_readme[0])
    assert not conf._long_read
    assert not conf._long_read_in_setup


if __name__ == "__main__":
    pytest.main(["-rx", "-v", "--pdb", __file__])
