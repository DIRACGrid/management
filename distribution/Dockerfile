# This dockerfile creates an image used for creating DIRAC tarballs
# Needs Java, Sencha, ExtJS for the web

# Based on Ubuntu
FROM ubuntu:latest
MAINTAINER Federico Stagni <federico.stagni@cern.ch>

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

# Sencha + ExtJS
ADD http://cdn.sencha.com/cmd/7.0.0.40/no-jre/SenchaCmd-7.0.0.40-linux-amd64.sh.zip .
RUN unzip SenchaCmd-7.0.0.40-linux-amd64.sh.zip
RUN chmod +x SenchaCmd-7.0.0.40-linux-amd64.sh
RUN ./SenchaCmd-7.0.0.40-linux-amd64.sh -q
#COPY ext-6.2.0/ext-6.2.0/ ext-6.2.0/
ADD http://cdn.sencha.com/ext/gpl/ext-6.2.0-gpl.zip .
RUN unzip ext-6.2.0-gpl.zip

# Now the "app"
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt
COPY . .
ADD https://raw.githubusercontent.com/DIRACGrid/DIRAC/integration/Core/scripts/dirac-install.py dirac_install.py
