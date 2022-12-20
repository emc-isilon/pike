FROM quay.io/pypa/manylinux2010_x86_64
COPY . /src/pike
RUN yum install -y krb5-devel krb5-workstation python27 && \
    source /opt/rh/python27/enable && \
    python2.7 -m pip install -U 'pip<21' && \
    python2.7 -m pip install build

CMD /src/pike/buildwheel/wheel27.sh
