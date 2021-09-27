#!/usr/bin/env bash

# build compiled wheel versions of pike with multiple different python versions

# ensure system build requirements are met (see README.md)

# any additional arguments supplied will be passed to the final
# `setup.py bdist_wheel` command and may be used to upload the
# packages to artifactory
#  ./build_all_wheels.sh upload -r http://artifactory01.prod.sea1.west.isilon.com/artifactory/api/pypi/pypi-local

# recommend the use of `pyenv` to install and activate
# multiple python versions before running the script.

set -euo pipefail

# XXX: py3.9 not supported by internal artifactory
versions=(python2 python3.6 python3.7 python3.8)

for v in ${versions[@]}
do
    rm -rf .build/$v && \
    virtualenv -p $v .build/$v && \
    .build/$v/bin/pip install 'build' && \
    .build/$v/bin/python -m build && \
    .build/$v/bin/python setup.py bdist_wheel $*
    # FIXME: ISILONEAT-1456, ISILONQE-3348
    # Code fix to let twine upload to local artifactory
    #.build/$v/bin/python -m build --outdir dist/ .
    #.build/$v/bin/pip install twine
    #.build/$v/bin/twine $* dist/*
done
