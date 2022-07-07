#!/usr/bin/env bash

# build compiled wheel versions of pike with multiple different python versions

# ensure system build requirements are met (see README.md)

# recommend the use of `pyenv` to install and activate
# multiple python versions before running the script.

set -euo pipefail

versions=(python2 python3.6 python3.7 python3.8 python3.9 python3.10)

rm -rf dist
for v in ${versions[@]}
do
    $v -m pip install --user 'build[virtualenv]' && $v -m build
done

cat <<EOF
To upload packages run:
python3 -m pip install --user twine
python3 -m twine upload dist/* --repository-url "<my-private-repo>"'
EOF
