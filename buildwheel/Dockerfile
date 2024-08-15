FROM quay.io/pypa/manylinux2010_x86_64
COPY . /src/pike
RUN sed -i 's/mirrorlist/#mirrorlist/g' /etc/yum.repos.d/CentOS-*
RUN sed -i 's|#baseurl=http://mirror.centos.org|baseurl=http://vault.centos.org|g' /etc/yum.repos.d/CentOS-*
RUN yum install -y krb5-devel krb5-workstation python27
RUN source /opt/rh/python27/enable
RUN export PATH=$PATH:/opt/rh/python27/root/usr/bin
RUN ls /opt/rh/python27/root/usr/bin/python2.7
RUN whereis libpython2.7.so.1.0
RUN export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/opt/rh/python27/root/usr/lib64
RUN echo /opt/rh/python27/root/usr/lib64 >> /etc/ld.so.conf
RUN ldconfig
RUN /opt/rh/python27/root/usr/bin/python2.7 -m pip install --trusted-host pypi.python.org -U 'pip<21'
RUN /opt/rh/python27/root/usr/bin/python2.7 -m pip install --trusted-host pypi.python.org build

CMD /src/pike/buildwheel/wheel27.sh
