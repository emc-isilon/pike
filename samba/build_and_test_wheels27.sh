#!/usr/bin/env bash

set -euxo pipefail

SCRIPT=$(readlink -f "$0")
SCRIPTPATH=$(dirname "$SCRIPT")
cd $SCRIPTPATH/..

docker build -t pike-buildwheel -f buildwheel/Dockerfile .
docker run -e HOST_IPV4 -e SAMBA_REALM -e SAMBA_SERVER -e ADMIN_PASSWORD \
       -v $SCRIPTPATH/../wheelhouse:/wheelhouse pike-buildwheel
