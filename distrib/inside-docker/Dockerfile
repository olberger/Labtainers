# Attempt at rebuilding the Labtainers distribution from inside a Docker container
FROM debian:latest

# Installation of base packets
RUN echo 'debconf debconf/frontend select Noninteractive' | debconf-set-selections
RUN apt-get update && apt-get upgrade -y && apt-get install -y --no-install-recommends ca-certificates sudo locales

RUN sudo apt-get install -y --no-install-recommends \
    git less python make g++
RUN sudo apt-get install -y \
    texlive-latex-base texlive-generic-recommended texlive-latex-extra

# Locales update
RUN rm -rf /var/lib/apt/lists/* \
    && localedef -i en_US -c -f UTF-8 -A /usr/share/locale/locale.alias en_US.UTF-8
ENV LANG en_US.utf8
ENV LANGUAGE en_US:en  
ENV LC_ALL en_US.UTF-8 

# Dynamic copy of group_id "docker"
# ARG DOCKER_GROUP_ID
RUN groupadd docker

# Adding user labtainer
RUN useradd -ms /bin/bash labtainer && sed -i "21i\labtainer ALL=(root) NOPASSWD:ALL\n" /etc/sudoers
RUN usermod -aG docker labtainer
USER labtainer
WORKDIR /home/labtainer

RUN git clone https://github.com/mfthomps/Labtainers.git

