#!/usr/bin/env bash

# source before bash "strict mode"
source /opt/rh/python27/enable

set -euxo pipefail

# build py27 wheel
cd /src/pike
python2.7 -m build
auditwheel repair dist/*.whl

# Test the wheel
export PIKE_SERVER=$SAMBA_SERVER
export PIKE_SHARE=s1

./samba/krb5.conf.sh
python2.7 -m pip install wheelhouse/*-cp27*.whl
python2.7 -m unittest pike.test.session

# if the wheelhouse dir is mounted, copy tested wheels to host
[[ -d /wheelhouse ]] && cp wheelhouse/* /wheelhouse/
