FROM quay.io/pypa/manylinux2010_x86_64
COPY . /src/pike
RUN sed -i 's/mirrorlist/#mirrorlist/g' /etc/yum.repos.d/CentOS-*
RUN sed -i 's|#baseurl=http://mirror.centos.org|baseurl=http://vault.centos.org|g' /etc/yum.repos.d/CentOS-*
RUN yum install -y krb5-devel krb5-workstation python27
RUN source /opt/rh/python27/enable
RUN export PATH=$PATH:/opt/rh/python27/root/usr/bin
RUN python2.7 -m pip install -U 'pip<21'
RUN python2.7 -m pip install build

CMD /src/pike/buildwheel/wheel27.sh
