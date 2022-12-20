#!/usr/bin/env bash

set -euxo pipefail

cat - | tee -a /etc/hosts <<EOF
$HOST_IPV4  $SAMBA_REALM
$HOST_IPV4  $SAMBA_SERVER
EOF

cat - | tee /etc/krb5.conf <<EOF
[libdefaults]
  default_realm = $SAMBA_REALM

[realms]
$SAMBA_REALM = {
  kdc = $SAMBA_SERVER
}
EOF
printf "$ADMIN_PASSWORD\n" | kinit administrator
