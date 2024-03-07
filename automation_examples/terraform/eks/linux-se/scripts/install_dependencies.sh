#!/bin/bash
apt-get update
apt-get install -y apt-transport-https ca-certificates curl  gnupg-agent  software-properties-common python
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
apt-get update && apt-get install -y docker-ce
