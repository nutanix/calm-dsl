#!/bin/bash

#Variables used in this script 
OPENLDAP_PASSWORD="@@{OPENLDAP_PASSWORD}@@"
UID="@@{UID}@@"
SECOND_LEVEL_DOMAIN_NAME="@@{SECOND_LEVEL_DOMAIN_NAME}@@"
TOP_LEVEL_DOMAIN_NAME="@@{TOP_LEVEL_DOMAIN_NAME}@@"

ldapdelete -w ${OPENLDAP_PASSWORD} -D "cn=ldapadm,dc=${SECOND_LEVEL_DOMAIN_NAME},dc=${TOP_LEVEL_DOMAIN_NAME}" "uid=${UID},ou=People,dc=${SECOND_LEVEL_DOMAIN_NAME},dc=${TOP_LEVEL_DOMAIN_NAME}"
echo "user @@{UID}@@ deleted!" >> ~/status.txt
sudo cat ~/status.txt