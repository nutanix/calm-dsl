#!/bin/bash
#Preperation
sudo yum update -y
sudo yum install gcc flex bison zlib libpcap pcre libdnet tcpdump -y 
sudo ln -s /usr/lib64/libdnet.so.1.0.1 /usr/lib64/libdnet.1

#Installing daq and snort 
BASE_URL="https://www.snort.org/downloads/snort/"
SNORT_PACKAGE_NAME=`curl https://snort.org/downloads\#snort-downloads | grep 'snort.*.centos8.x86_64.rpm'|grep -v openappid | cut -d\> -f2 | cut -d\< -f1`
URL="$BASE_URL$SNORT_PACKAGE_NAME"
sudo yum install $URL -y

#Updating the shared libraries
sudo ldconfig

#Set the permissions
sudo chmod -R 5775 /etc/snort
sudo chmod -R 5775 /var/log/snort
sudo mkdir -p /usr/local/lib/snort_dynamicrules
sudo chmod -R 5775 /usr/local/lib/snort_dynamicrules
sudo chown -R snort:snort /etc/snort
sudo chown -R snort:snort /var/log/snort
sudo chown -R snort:snort /usr/local/lib/snort_dynamicrules


#Create white and blacklists
sudo touch /etc/snort/rules/white_list.rules
sudo touch /etc/snort/rules/black_list.rules
sudo touch /etc/snort/rules/local.rules

#Using community rules
sudo yum install wget -y
sudo wget https://www.snort.org/rules/community -O ~/community.tar.gz
sudo tar -xvf ~/community.tar.gz -C ~/
sudo cp ~/community-rules/* /etc/snort/rules
sudo sed -i 's/include \$RULE\_PATH/#include \$RULE\_PATH/' /etc/snort/snort.conf

#Configuring the network and rule sets
IP=$(/usr/sbin/ip addr | grep inet | grep eth0 | awk '{print $2}')
echo $IP
sudo sed -i 's#ipvar HOME_NET any#ipvar HOME_NET '$IP'#' /etc/snort/snort.conf
sudo sed -i 's/ipvar EXTERNAL_NET any/ipvar EXTERNAL_NET !$HOME_NET/' /etc/snort/snort.conf
sudo sed -i 's#var SO_RULE_PATH ../so_rules#var SO_RULE_PATH /etc/snort/so_rules#' /etc/snort/snort.conf
sudo sed -i 's#var PREPROC_RULE_PATH ../preproc_rules#var PREPROC_RULE_PATH /etc/snort/preproc_rules#' /etc/snort/snort.conf
sudo sed -i 's#var WHITE_LIST_PATH ../rules#var WHITE_LIST_PATH /etc/snort/rules#' /etc/snort/snort.conf
sudo sed -i 's#var BLACK_LIST_PATH ../rules#var BLACK_LIST_PATH /etc/snort/rules#' /etc/snort/snort.conf
sudo sed -i '/output unified2/s/^#//g' /etc/snort/snort.conf
sudo sed -i '/local.rules/s/^#//g' /etc/snort/snort.conf
echo 'include $RULE_PATH/community.rules' >> sudo tee -a /etc/snort/snort.conf

#Validating settings
sudo snort -T -c /etc/snort/snort.conf

#Starting service
sudo systemctl start snortd
sudo systemctl status snortd


