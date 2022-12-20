FROM quay.io/pypa/manylinux2010_x86_64
COPY . /src/pike
RUN yum install -y krb5-devel krb5-workstation python27 && \
    source /opt/rh/python27/enable && \
    python2.7 -m pip install -U 'pip<21' && \
    python2.7 -m pip install build

CMD source /opt/rh/python27/enable && \
    cd /src/pike && \
    python2.7 -m build && \
    auditwheel repair dist/*.whl && \
    /src/pike/samba/krb5.conf.sh && \
    export PIKE_SERVER=$SAMBA_SERVER && \
    export PIKE_SHARE=s1 && \
    python2.7 -m pip install wheelhouse/*-cp27*.whl && \
    python -m unittest pike.test.session
