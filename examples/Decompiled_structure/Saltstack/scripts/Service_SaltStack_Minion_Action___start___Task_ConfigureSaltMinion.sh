#!/bin/sh

# Install the repo for the latest SaltStack version
sudo yum -y install https://repo.saltstack.com/yum/redhat/salt-repo-latest-2.el7.noarch.rpm

# Install the actual SaltStack minion
sudo yum -y install salt-minion

sudo echo '@@{SaltStackMaster.address}@@ salt' | sudo tee -a /etc/hosts

# Enable and start salt-minion service 
sudo systemctl enable salt-minion.service
sudo systemctl start salt-minion.service