#
#   Simple extension of Alma9 with git, openssl and runit
#
#..................................................................
FROM cern/alma9-base:latest
ARG RUNIT_RPM=runit-2.1.2-2.el9.x86_64.rpm

RUN yum install -y git freetype fontconfig pixman libXrender psmisc python3 && \
    yum localinstall -y "http://diracproject.web.cern.ch/diracproject/rpm/${RUNIT_RPM}" && \
    yum clean all && \
    rm -rf /var/lib/apt/lists/* /lib/modules/* /lib/firmware/* /lib/kbd /var/cache/yum

CMD ["/usr/sbin/init"]
