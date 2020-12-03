FROM centos:6
LABEL maintainer="marko.petric@cern.ch"
ENV container docker

# Remove obsolete repos
RUN rm -rf /etc/yum.repos.d/*

# Install enabled Vault Repo
COPY CentOS-Vault.repo /etc/yum.repos.d/CentOS-Vault.repo

# Install EPEL 
RUN yum install -y epel-release

# Install DIRACOS requirements
RUN yum install -y mock rpm-build fedora-packager createrepo python-pip

# Run bash as user default command
CMD ["/bin/bash"]
