#!/bin/sh

#Variables used in this script 
SECOND_LEVEL_DOMAIN_NAME="@@{SECOND_LEVEL_DOMAIN_NAME}@@"
TOP_LEVEL_DOMAIN_NAME="@@{TOP_LEVEL_DOMAIN_NAME}@@"
READONLY_USER="@@{READONLY_USER}@@"
OpenLDAPServer_address="@@{OpenLDAPServer.address}@@"

#Yum update and upgrade
sudo yum -y update
sudo yum -y upgrade

#Install required packages
sudo yum -y install net-tools bind-utils bash-completion nano firewalld
sudo echo "yum updates completed!" >> ~/status.txt

#Set hostname
sudo hostnamectl set-hostname openldap-client
sudo echo "hostname configured!" >> ~/status.txt

#Install openldap client and config
sudo yum install -y openldap-clients nss-pam-ldapd
sudo authconfig --enableldap --enableldapauth --ldapserver=${OpenLDAPServer_address} --ldapbasedn="dc=${SECOND_LEVEL_DOMAIN_NAME},dc=${TOP_LEVEL_DOMAIN_NAME}" --enablemkhomedir --update
sudo systemctl restart nslcd
sudo getent passwd ${READONLY_USER} >> ~/status.txt