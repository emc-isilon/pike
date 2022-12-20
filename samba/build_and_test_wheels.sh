#!/usr/bin/env bash

set -euxo pipefail

SCRIPT=$(readlink -f "$0")
SCRIPTPATH=$(dirname "$SCRIPT")
cd $SCRIPTPATH/..

python3 -m cibuildwheel --platform linux "$@"