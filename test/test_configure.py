"""Tests for the configure functions in pypackage."""


import sys
import mock
import pytest

from pypackage import configure
from pypackage.config import Config
from pypackage.cmdline import get_options


def test_ask_for_value():
    """Ensure we correctly prompt the user."""

    with mock.patch.object(configure, "INPUT", return_value="ok") as inp_patch:
        assert configure.ask_for_value("foo") == "ok"
    inp_patch.assert_called_once_with("Please enter the value for foo: ")


def test_ask_for_value__empty_str_is_none():
    """If the user hits enter without input, None should be returned."""

    with mock.patch.object(configure, "INPUT", return_value=""):
        assert configure.ask_for_value("foo") is None


def test_ask_for_value__interrupt_quits():
    """SystemExit should be raised if the user sends ^C."""

    with mock.patch.object(configure, "INPUT", side_effect=KeyboardInterrupt):
        with pytest.raises(SystemExit) as error:
            configure.ask_for_value("foo")
    assert error.value.args[0] == "Cancelled on user request"


def test_value_in_config__classifiers(capfd):
    """The key 'classifiers' should be handled."""

    conf = Config()
    with mock.patch.object(configure, "handle_classifiers", return_value="ok"):
        configure.set_value_in_config("classifiers", conf, conf._KEYS)
    out, err = capfd.readouterr()
    assert out == "classifiers set to: ['ok']\n"
    assert not err


def test_value_in_config__not_classifiers(capfd):
    """Any other key should be the same."""

    conf = Config()
    with mock.patch.object(configure, "ask_for_value", return_value="Frank"):
        configure.set_value_in_config("author", conf, conf._KEYS)
    out, err = capfd.readouterr()
    assert out == "author set to: 'Frank'\n"
    assert not err


def test_value_in_config__invalid_try_again():
    """If the return from the user is invalid, they should be re-prompted."""

    conf = Config()
    user_input_patch = mock.patch.object(
        configure,
        "ask_for_value",
        side_effect=iter([
            "{'what': 12.3",     # malformed input
            "{'what': 1 / 4}",   # valid input, but not for the spec
            "{'what': ['ok']}",  # valid input
        ])
    )
    with user_input_patch:
        configure.set_value_in_config("entry_points", conf, conf._KEYS)

    assert conf.entry_points == {"what": ["ok"]}


def test_invalid__feedback(capfd):
    """The user should receive some feedback when the value doesn't coerce."""

    class TestObject(object):
        def __init__(self):
            self.str_count = 0

        def __str__(self):
            self.str_count += 1
            if self.str_count == 1:
                raise IOError
            else:
                return "test object"

    conf = Config(name="foo")
    coerce_patch = mock.patch.object(
        configure,
        "coerce_to_expected",
        return_value=TestObject(),
    )

    with mock.patch.object(configure, "ask_for_value"):
        with coerce_patch:
            configure.set_value_in_config("name", conf, conf._KEYS)

    out, err = capfd.readouterr()
    assert "name as test object failed to verify. should be str" in err
    assert "name set to: 'test object'\n" == out


@pytest.mark.parametrize("value", (None, False, 0, ""))
def test_coerce__no_value(value):
    """If the value fails a truthyness test, it should be returned."""

    assert configure.coerce_to_expected(value, "foo", str) == value


@pytest.mark.parametrize("value, expected", [
    ("None", False),
    ("something", True),
    ("1", True),
    ("0", False),
    ("false", True),
    ("False", False),
])
def test_coerce__to_bool(value, expected):
    """Ensure we are properly coercing to boolean."""

    assert configure.coerce_to_expected(value, "foo", bool) is expected


@pytest.mark.parametrize("value, expected", [(15.16, "15.16"), (True, "True")])
def test_coerce__to_str(value, expected):
    """Ensure we coerce to str."""

    assert configure.coerce_to_expected(value, "foo", str) == expected


def test_coerce_to_list_sorts():
    """Ensure coerce to list returns a sorted list if it's already a list."""

    assert configure.coerce_to_list(["foo", "bar", "baz", "potato"]) == [
        "bar", "baz", "foo", "potato"
    ]


@pytest.mark.parametrize("value", ",;:| ")
def test_corce_to_list_splits(value):
    """Ensure words joined with any of the value chars are split by coerce."""

    phrase = "In the beginning were the Words".split()
    assert configure.coerce_to_list(value.join(phrase)) == [
        "In",
        "Words",
        "beginning",
        "the",
        "the",
        "were",
    ]


def test_standard_attributes(reset_sys_argv, move_home_pypackage):
    """Ensure the standard attribute set."""

    conf = Config()
    expected_attrs = list(conf._KEYS.keys())[:17]
    conf.name = "foobar"
    conf.classifiers = ["fake classifier"]
    expected_attrs.remove("name")
    expected_attrs.remove("classifiers")
    attrs = configure.standard_attributes(conf, get_options())
    assert attrs == expected_attrs


def test_standard_attributes__re_config(reset_sys_argv):
    """If reconfig is set, all standard attributes should be unconfigured."""

    conf = Config()
    conf.name = "something"
    sys.argv = ["py-build", "-r"]
    attrs = configure.standard_attributes(conf, get_options())
    expected = list(conf._KEYS.keys())[:17]
    assert attrs == expected


def test_standard_attributes__re_classify(reset_sys_argv):
    """If reclassify is set, classifiers should be in the unconfigured set."""

    conf = Config()
    conf.classifiers = ["fake things"]
    sys.argv = ["py-build", "-R"]
    attrs = configure.standard_attributes(conf, get_options())
    assert "classifiers" in attrs


def test_feature_attributes(reset_sys_argv, move_home_pypackage):
    """If we have default runner args they should appear unconfigured."""

    conf = Config()
    conf.runner_args = ["fake", "args"]
    conf._configured_runner_args = False
    attrs = configure.feature_attributes(conf, get_options())
    expected = list(conf._PYPACKAGE_KEYS.keys())
    assert attrs == expected


def test_feature_attributes__re_config(reset_sys_argv):
    """When --rebuild is used, all features should appear unconfigured."""

    conf = Config()
    conf.test_runner = "pytest"
    sys.argv = ["py-build", "--rebuild"]
    attrs = configure.feature_attributes(conf, get_options())
    expected = list(conf._PYPACKAGE_KEYS.keys())
    assert attrs == expected


def test_extended_attributes(reset_sys_argv, move_home_pypackage):
    """Extended attributes should return any unset keys past 17."""

    conf = Config()
    expected = list(conf._KEYS.keys())[17:]
    conf.use_2to3 = True
    expected.remove("use_2to3")
    attrs = configure.extended_attributes(conf, get_options())
    assert attrs == expected


def test_extended_attributes__re_config(reset_sys_argv):
    """If --rebuild is used, all extended attributes should be unconfigured."""

    conf = Config()
    conf.use_2to3 = True
    sys.argv = ["py-build", "-r"]
    attrs = configure.extended_attributes(conf, get_options())
    expected = list(conf._KEYS.keys())[17:]
    assert attrs == expected


@pytest.mark.parametrize(
    "flags, banner",
    [
        ("-e", "Starting interactive build..."),
        ("-re", "Reconfiguring..."),
    ],
    ids=("extended/normal", "re-build")
)
def test_interactive_setup(capfd, reset_sys_argv, move_home_pypackage,
                           flags, banner):
    """Ensure the calls made and feedback during the interactive setup."""

    conf = Config()
    sys.argv = ["py-build", flags]
    opts = get_options()

    standard_patch = mock.patch.object(
        configure,
        "standard_attributes",
        return_value=["standard"],
    )
    feature_patch = mock.patch.object(
        configure,
        "feature_attributes",
        return_value=["feature"],
    )
    extended_patch = mock.patch.object(
        configure,
        "extended_attributes",
        return_value=["extended"],
    )
    set_value_patch = mock.patch.object(configure, "set_value_in_config")

    with standard_patch:
        with feature_patch:
            with extended_patch:
                with set_value_patch as patched_set_value:
                    assert configure.run_interactive_setup(conf, opts) == conf

    expected_calls = [
        mock.call.Call("standard", conf, conf._KEYS),
        mock.call.Call("feature", conf, conf._PYPACKAGE_KEYS),
        mock.call.Call("extended", conf, conf._KEYS),
    ]
    assert patched_set_value.mock_calls == expected_calls

    out, err = capfd.readouterr()
    assert banner in out
    assert "~ Standard Attributes ~" in out
    assert "~ Pypackage Features ~" in out
    assert "~ Extended Attributes ~" in out
    assert not err


if __name__ == "__main__":
    pytest.main(["-rx", "-vv", "--pdb", __file__])
