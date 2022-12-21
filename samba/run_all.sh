#!/usr/bin/env bash

# run this inside of a container to kick off the tests

set -euxo pipefail

SCRIPT=$(readlink -f "$0")
SCRIPTPATH=$(dirname "$SCRIPT")

$SCRIPTPATH/krb5.conf.sh

export PIKE_SERVER=$SAMBA_SERVER
export PIKE_SHARE=s1
python3 -m pip install /src/pike
python3 -m unittest pike.test.samba_suite
pytest -ra
