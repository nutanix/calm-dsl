#!/bin/bash
set -ex

sudo yum install -y --quiet lvm2 libudev-devel
sudo pvcreate /dev/sdb
sudo vgcreate chef_vg /dev/sdb
sleep 3
sudo lvcreate -l 100%VG -n chef_lvm chef_vg
sudo mkfs.xfs /dev/chef_vg/chef_lvm

echo -e "/dev/chef_vg/chef_lvm \t /opt \t xfs \t defaults \t 0 0" | sudo tee -a /etc/fstab
sudo mount -a

sudo yum install -y --quiet wget

curl -L https://www.chef.io/chef/install.sh | sudo bash

sudo mkdir -p /var/chef/cache /var/chef/cookbooks

wget -qO- https://supermarket.chef.io/cookbooks/chef-server/versions/5.5.2/download | sudo tar xvzC /var/chef/cookbooks

for dep in chef-ingredient
do
      wget -qO- https://supermarket.chef.io/cookbooks/${dep}/download | sudo tar xvzC /var/chef/cookbooks
  done

  cat > /tmp/dna.json <<EOH
  {
    "chef-server": {
    "api_fqdn": "chef-server",
    "addons": ["manage"],
    "accept_license": true,
    "version": "@@{CHEF_SERVER_VERSION}@@"
  }
}
EOH

# GO GO GO!!!
sudo chef-solo --chef-license accept-silent -o 'recipe[chef-server::default],recipe[chef-server::addons]' -j /tmp/dna.json
