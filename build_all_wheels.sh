#!/usr/bin/env bash

# build compiled wheel versions of pike with multiple different python versions

# ensure system build requirements are met (see README.md)

# any additional arguments supplied will be passed to the final
# `setup.py bdist_wheel` command and may be used to upload the
# packages to artifactory

# recommend the use of `pyenv` to install and activate
# multiple python versions before running the script.

set -euo pipefail

# XXX: py27 kerb support is broken
versions=(python3.6 python3.7 python3.8 python3.9 python3.10)

python3.10 -m pip install twine
rm -rf .build dist
for v in ${versions[@]}
do
    $v -m pip install -U pip && \
    $v -m pip install 'build[virtualenv]' && \
    $v -m build
done

echo 'To upload run: python3.10 -m twine upload dist/* --repository-url "<my-private-repo>"'
