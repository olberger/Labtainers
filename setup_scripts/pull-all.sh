#!/bin/bash
#
# pull the baseline labtainer images from the appropriate registry
# NOTE use of environment variable TEST_REGISTRY
# Script assumes the pwd is the parent of the labtainer directory
# Intended to be called from update-labtainer.sh
#
if [ "$TEST_REGSISTRY" == YES ]; then
    registry=$(grep TEST_REGISTRY labtainer/trunk/config/labtainer.config | cut -f 2)
else
    registry=$(grep DEFAULT_REGISTRY labtainer/trunk/config/labtainer.config | cut -f 2)
fi
docker pull $registry/labtainer.base
docker pull $registry/labtainer.network
docker pull $registry/labtainer.firefox
docker pull $registry/labtainer.wireshark
docker pull $registry/labtainer.java
docker pull $registry/labtainer.centos
docker pull $registry/labtainer.lamp
