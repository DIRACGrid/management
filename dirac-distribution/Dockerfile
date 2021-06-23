# This dockerfile creates an image used for creating and uploading DIRAC tarballs
#
# Python3 code
# Needs git, subversion, mercurial for getting the code of DIRAC and its extensions
# Needs Java, Sencha, ExtJS for compiling WebAppDIRAC and its extensions
# Needs kerberos for uploading the tarballs

# Based on Ubuntu
FROM ubuntu:latest
LABEL org.opencontainers.image.authors="federico.stagni@cern.ch"

# Updates, plus install Java (for Sencha), and python3 (+pip)
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y openjdk-8-jdk && \
    apt-get install -y ant && \
    apt-get install -y unzip && \
    apt-get install -y python3 && \
    apt-get install -y python3-pip && \
    apt-get install -y git && \
    apt-get install -y subversion && \
    apt-get install -y mercurial && \
    apt-get clean;

# For uploading the tarballs we use kerberos
RUN DEBIAN_FRONTEND='noninteractive' apt-get install -y krb5-user
ADD http://linux.web.cern.ch/linux/docs/krb5.conf /etc/krb5.conf
RUN echo "   GSSAPIDelegateCredentials yes" >> /etc/ssh/ssh_config && \
    echo "   GSSAPITrustDNS yes" >> /etc/ssh/ssh_config && \
    echo "   StrictHostKeyChecking no" >> /etc/ssh/ssh_config

# Sencha + ExtJS
ADD http://cdn.sencha.com/cmd/7.0.0.40/no-jre/SenchaCmd-7.0.0.40-linux-amd64.sh.zip .
RUN unzip SenchaCmd-7.0.0.40-linux-amd64.sh.zip && \
    chmod +x SenchaCmd-7.0.0.40-linux-amd64.sh && \
    ./SenchaCmd-7.0.0.40-linux-amd64.sh -q
ADD http://cdn.sencha.com/ext/gpl/ext-6.2.0-gpl.zip .
RUN unzip ext-6.2.0-gpl.zip
# Give everyone the same permissions on the ExtJS sources so the image can be ran as any user
RUN chmod -R a=u /ext-6.2.0/ /root && chmod a+rwx /root/bin/Sencha/Cmd
ENV PATH /root/bin/Sencha/Cmd:$PATH

# Now the "app"
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt
COPY . .
ADD https://raw.githubusercontent.com/DIRACGrid/management/master/dirac-install.py dirac_install.py
