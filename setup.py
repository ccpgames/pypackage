"""Pypackage's setup.py"""


import io
from setuptools import setup
from setuptools import find_packages
from setuptools.command.test import test as TestCommand


class PyTest(TestCommand):
    """TestCommand subclass to use pytest with setup.py test."""

    def finalize_options(self):
        """Find our package name and test options to fill out test_args."""

        TestCommand.finalize_options(self)
        self.test_args = ["-v", "-rx", "--cov-report", "term-missing", "--cov",
                          "pypackage", "test"]
        self.test_suite = True

    def run_tests(self):
        """pytest discovery and test execution."""

        import pytest
        raise SystemExit(pytest.main(self.test_args))


def long_description():
    with io.open("README.rst", "r", encoding="utf-8") as openreadme:
        return openreadme.read()


setup(
    name="pypackage",
    version="0.1.6",
    author="Adam Talsma",
    author_email="se-adam.talsma@ccpgames.com",
    url="http://ccpgames.github.io/pypackage",
    download_url="https://github.com/ccpgames/pypackage",
    description="Pypackage looks to package python without writing a setup.py",
    long_description=long_description(),
    packages=find_packages(exclude=["test"]),
    package_data={"pypackage": ["pypackage/classifiers"]},
    include_package_data=True,
    install_requires=[
        "wheel      >= 0.24.0",
        "setuptools >= 15.0",
        "pytest     >= 2.7.0",
        "nose       >= 1.3.0",
        "PyYAML     >= 3.0",
    ],
    cmdclass={"test": PyTest},
    tests_require=["mock", "pytest", "pytest-cov", "requests"],
    entry_points={"console_scripts": [
        "py-build   = pypackage.commands:build",
        "py-develop = pypackage.commands:develop",
        "py-install = pypackage.commands:install",
        "py-setup   = pypackage.commands:setup",
        "py-test    = pypackage.commands:run_tests",
    ]},
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Environment :: Console :: Curses',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Topic :: Software Development',
        'Topic :: Software Development :: Code Generators',
        'Topic :: System :: Archiving :: Packaging',
        'Topic :: System :: Installation/Setup',
        'Topic :: System :: Software Distribution',
        'Topic :: Utilities'
    ],
)
