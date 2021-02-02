#
#   Simple extension of CC7 with GridFTP and gsissh
#
#..................................................................
FROM cern/cc7-base:latest

# Add the EGI trustanchors and CAs
ADD http://repository.egi.eu/sw/production/cas/1/current/repo-files/EGI-trustanchors.repo /etc/yum.repos.d/EGI-trustanchors.repo
RUN yum install -y ca-policy-egi-core

RUN yum install -y globus-ftp-client gsissh gsi-openssh-clients voms-clients
