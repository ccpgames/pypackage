"""Tests for the classifier selection process."""


import os
import mock
import pytest

from pypackage.config import Config

try:
    from pypackage import classified
    HAS_CURSES = True
except ImportError:
    HAS_CURSES = False


@pytest.mark.skipif(not HAS_CURSES, reason="no curses support")
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


@pytest.mark.skipif(not HAS_CURSES, reason="no curses support")
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


@pytest.mark.skipif(not HAS_CURSES, reason="no curses support")
def test_back_it_up():
    """Ensure we navigate the quasi singly linked list correctly."""

    all_classifiers = classified.read_classifiers()
    parent = all_classifiers.classifiers[8].classifiers[2]
    child = parent.classifiers[1]
    assert classified.back_it_up(child, all_classifiers) == parent


if __name__ == "__main__":
    pytest.main(["-rx", "-v", "--pdb", __file__])
