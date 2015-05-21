#!/bin/bash

#
# This script will create a new venv and install pypackage inside it.
# It then creates three example packages, all inside a new example
# directory. The hello-world package should be installed, the tested_mod and
# tested_pkg packages should only be tested and built. The has_data package
# should also be installed and should have a script entry point of `read_data`
# which should dump 100B of static random data to stdout.
#
# Make sure to re-activate the venv after running this script with:
#
#  $ source example/bin/activate
#
# then you can inspect the installed state of the demo packages
#

#
# cleanup and setup
#
rm -rf example
virtualenv --python=python2.7 --no-site-packages example
source example/bin/activate
pip install pypackage
cd example

#
# Create hello-world
#
mkdir hello-world
cd hello-world
cat <<EOF > my_module.py
def my_function():
    return "my_module is correctly installed"
EOF

#
# Install hello-world
#
py-install

# verify the install
cd ..
python -c 'import my_module; print(my_module.my_function())'

#
# Create tested_mod
#
mkdir tested_mod
cd tested_mod

# make the tests
mkdir tests
cd tests
cat <<EOF > test_tested_mod.py
import pytest

import tested_mod

def test_returns_true():
    assert tested_mod.returns_true()

def test_returns_false():
    assert tested_mod.returns_false() is False
EOF
cd ..

# make the module
cat <<EOF > tested_mod.py
def returns_true():
    return True

def returns_false():
    return False
EOF

# inform pypackage
cat <<EOF > pypackage.meta
{"test_runner": "pytest"}
EOF

# run the tests
py-test

# build a release
py-build

# show results
ls -lh dist
cd ..

#
# Create tested_pkg
#

# create the directories
mkdir tested_pkg
cd tested_pkg
mkdir tested_pkg
mkdir tests

# write the package files
cd tested_pkg
touch __init__.py
cat <<EOF > some_mod.py
def is_true():
    return True
def is_none():
    return None
EOF
cd ..

# write the test file
cd tests
cat <<EOF > test_some_mod.py
import pytest
from tested_pkg import some_mod

def test_is_true():
    assert some_mod.is_true()

def test_is_none():
    assert some_mod.is_none() is None
EOF
cd ..

# write the pypackage.meta
cat <<EOF > pypackage.meta
# we only have to supply packages here because we have test in our name
{"test_runner": "pytest", "packages": "tested_pkg", "version": "1.0.0"}
EOF

# run tests
py-test

# create releases
py-build

# save a copy of the setup.py in the src
py-build -s
cd ..

#
# data project
#

mkdir -p has_data/has_data/data
cd has_data/has_data
touch __init__.py

# create data
dd if=/dev/random of=data/file bs=10 count=10

# create python module to read and display data
cat <<EOF > read_data.py
import os

def to_stdout():
    random_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "data", "file")
    print("your random data is:")
    with open(random_file) as random_data:
        print(random_data.read())
EOF
cd ..

# make a script, (you could use an entry point but this shows the auto pickup)
mkdir bin
cat <<EOF > bin/random_data
#!/usr/bin/env python

from has_data import read_data

if __name__ == "__main__":
    read_data.to_stdout()
EOF
chmod +x bin/random_data

echo '{"version": "1.0.0", "packages": "has_data"}' > pypackage.meta

py-install

random_data

echo "example packages created! use"
echo "  source example/bin/activate"
echo "to activate the example virtualenv"
