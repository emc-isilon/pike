#!/usr/bin/env bash

set -euxo pipefail

IF=$(/sbin/ip route|awk '/default/ { print $5 }')
export HOST_IPV4=$(ip -4 addr show $IF | grep -Po 'inet \K[\d.]+')
export SAMBADC_INTERFACES=$IF
export SAMBADC_HOSTNAME=dc
export SAMBA_WORKGROUP=PIKE
export SAMBA_REALM=${SAMBA_WORKGROUP}.TEST.LOCAL
export SAMBA_SERVER=${SAMBADC_HOSTNAME}.${SAMBA_REALM}

# Absolute path to this script, e.g. /home/user/bin/foo.sh
SCRIPT=$(readlink -f "$0")
# Absolute path this script is in, thus /home/user/bin
SCRIPTPATH=$(dirname "$SCRIPT")
cd $SCRIPTPATH

cat - > krb5.conf <<EOF
[libdefaults]
        default_realm = $SAMBA_REALM

[realms]
        $SAMBA_REALM = {
                kdc = $SAMBA_SERVER
        }
EOF

function cleanup ()
{
    docker compose down
    docker volume rm samba_lib samba_etc
}

trap cleanup EXIT
docker compose up
