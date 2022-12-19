# Samba DC environment

This environment exists for running tests using kerberos authentication.

## Requirements

The host requires `docker compose` installed and functional.

## Run All Tests

Using kerberos authentication:

```shell
./samba/dc.sh docker compose up runner
```

## Build Wheels

Must run on linux; will use docker containers for the build.

```shell
pip install --user cibuildwheel
./samba/dc.sh ./build_and_test_wheels.sh
```

After each wheel is built, it will be installed and used to establish a kerberos
session to the Samba DC.

Built wheels will be placed in pike/wheelhouse.