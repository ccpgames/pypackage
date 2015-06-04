"""Tests for the classifier selection process."""


import os
import mock
import pytest
import requests

from pypackage.config import Config

try:
    from pypackage import classified
    HAS_CURSES = True
except ImportError:
    HAS_CURSES = False


# this skips all tests in this module if the client doesn't have curses
pytestmark = pytest.mark.skipif(not HAS_CURSES, reason="no curses support")


def test_choose_classifiers(reset_sys_argv, simple_module):
    """Verify the logic in choosing classifiers."""

    os.environ.pop("ESCDELAY", None)
    conf = Config()
    box = mock.Mock()
    box.pick = mock.Mock(side_effect=iter([0, 4, 4, 4, 0, 9, 4, 3, 0, None]))

    with mock.patch.object(classified, "curses"):
        with mock.patch.object(classified, "BoxSelector", return_value=box):
            choices = classified.choose_classifiers(conf)

    assert choices == ["Development Status :: 4 - Beta"]
    assert "ESCDELAY" not in os.environ


def test_old_escdelay_persists(reset_sys_argv, simple_module):
    """Ensure any previously existing ESCDELAY envvar is reset on exit."""

    os.environ["ESCDELAY"] = "100"
    conf = Config()
    box = mock.Mock()
    box.pick = mock.Mock(return_value=None)

    with mock.patch.object(classified, "curses"):
        with mock.patch.object(classified, "BoxSelector", return_value=box):
            classified.choose_classifiers(conf)

    assert os.environ["ESCDELAY"] == "100"


def test_back_it_up():
    """Ensure we navigate the quasi singly linked list correctly."""

    all_classifiers = classified.read_classifiers()
    parent = all_classifiers.classifiers[8].classifiers[2]
    child = parent.classifiers[1]
    assert classified.back_it_up(child, all_classifiers) == parent


def test_classifiers_current():
    """Ensure the shipped classifiers file is synced with pypi."""

    packaged_trove_file = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "pypackage",
        "classifiers"
    )

    with open(packaged_trove_file) as opent:
        packaged = [t.strip() for t in opent.read().splitlines() if t]

    url = "https://pypi.python.org/pypi?:action=list_classifiers"
    trove_req = requests.get(url).text

    current = [t.strip() for t in trove_req.splitlines() if t]

    assert packaged == current, "curl {} > pypackage/classifiers".format(url)


if __name__ == "__main__":
    pytest.main(["-rx", "-v", "--pdb", __file__])
