FROM quay.io/pypa/manylinux2010_x86_64
COPY . /src/pike
RUN sed -i 's/mirrorlist/#mirrorlist/g' /etc/yum.repos.d/CentOS-* && \
    sed -i 's|#baseurl=http://mirror.centos.org|baseurl=http://vault.centos.org|g' /etc/yum.repos.d/CentOS-* && \
    yum install -y krb5-devel krb5-workstation python27 && \
    source /opt/rh/python27/enable && \
    export PATH=$PATH:/opt/rh/python27/root/usr/bin && \
    export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/opt/rh/python27/root/usr/lib64 && \
    echo /opt/rh/python27/root/usr/lib64 >> /etc/ld.so.conf && \
    ldconfig && \
    /opt/rh/python27/root/usr/bin/python2.7 -m pip install --trusted-host pypi.python.org -U 'pip<21' && \
    /opt/rh/python27/root/usr/bin/python2.7 -m pip install --trusted-host pypi.python.org build
CMD /src/pike/buildwheel/wheel27.sh
