#!/usr/bin/env bash

set -euxo pipefail

SCRIPT=$(readlink -f "$0")
SCRIPTPATH=$(dirname "$SCRIPT")

IF=$(/sbin/ip route|awk '/default/ { print $5 }')
export HOST_IPV4=$(ip -4 addr show $IF | grep -Po 'inet \K[\d.]+')
export SAMBADC_INTERFACES=$IF
export SAMBADC_HOSTNAME=dc
export SAMBA_WORKGROUP=PIKE
export SAMBA_REALM=${SAMBA_WORKGROUP}.TEST.LOCAL
export SAMBA_SERVER=${SAMBADC_HOSTNAME}.${SAMBA_REALM}
export ADMIN_PASSWORD=$(cat "$SCRIPTPATH/admin_password")

function cleanup ()
{
    docker compose down
    docker volume rm samba_lib samba_etc
}

trap cleanup EXIT
cd "$SCRIPTPATH"
docker compose up dc &
sleep 30
# pass off control to remaining args
"$@"
