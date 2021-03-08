#!/bin/bash

set -x
set -e

upload=$1

rm -rf dist/*
python setup.py develop sdist bdist_wheel
if [ "$upload" == "1" ]; then
    twine upload dist/*
fi
