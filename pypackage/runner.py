"""This file is slightly awkward. It contains the template for using a test
runner in a setup.py file, and a class for using it with setuptools directly.

The test runner can be one of pytest, nose, or unittest.
"""


import os
import unittest
from setuptools.command.test import test as TestCommand


class TestRunner(TestCommand):  # pragma: no cover
    """TestCommand subclass to use pytest or nose with setup.py test."""

    @staticmethod
    def pypackage(config):
        """Set with self when this runner is selected for direct testing."""

        TestRunner._pypackage = config

    def finalize_options(self):
        """Find our package name and test options to fill out test_args."""

        TestCommand.finalize_options(self)
        self.test_args = TestRunner._pypackage.runner_args
        self.test_suite = True

    def run_tests(self):
        """Run tests inline, could be any of pytest, nose or unittest."""

        if TestRunner._pypackage.test_runner == "nose":
            errno = TestRunner._pypackage._runner.main(argv=self.test_args)
        elif TestRunner._pypackage.test_runner == "unittest":
            test_suite = unittest.defaultTestLoader.discover(os.path.abspath(
                getattr(TestRunner._pypackage, "tests_dir", ".")
            ))
            errno = unittest.TextTestRunner().run(test_suite)
        else:
            errno = TestRunner._pypackage._runner.main(self.test_args)

        raise SystemExit(errno)


# for the setup.py; used in config outputting
_TEMPLATE = '''\
from setuptools.command.test import test as TestCommand


class PyPackageTest(TestCommand):
    """TestCommand subclass to enable setup.py test."""

    def finalize_options(self):
        """Find our package name and test options to fill out test_args."""

        TestCommand.finalize_options(self)
        self.test_args = {self.runner_args}
        self.test_suite = True

    def run_tests(self):
        """{self.test_runner} discovery and test execution."""

        import {self.test_runner}
'''


PYTEST_TEMPLATE = _TEMPLATE + \
    "{}raise SystemExit(pytest.main(self.test_args))\n\n".format(" " * 8)

NOSE_TEMPLATE = _TEMPLATE + \
    "{}raise SystemExit(nose.main(argv=self.test_args))\n\n".format(" " * 8)


# UNITTEST_TEMPLATE requires the extra tests_dir kwarg to be used with format
UNITTEST_TEMPLATE = _TEMPLATE + """\
        import os

        test_suite = unittest.defaultTestLoader.discover(
            os.path.abspath({tests_dir!r:})
        )
        raise SystemExit(unittest.TextTestRunner().run(test_suite))

"""
