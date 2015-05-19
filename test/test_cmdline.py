"""Ensure we are parsing arguments corretly."""


import sys
import pytest

from pypackage.cmdline import get_options


def test_get_options(reset_sys_argv):
    sys.argv = ["py-build", "-isR", "--extended"]
    options = get_options()
    for opt in ("interactive", "setup", "re_classify", "extended"):
        assert getattr(options, opt)


if __name__ == "__main__":
    pytest.main(["-rx", "-v", "--pdb", __file__])
