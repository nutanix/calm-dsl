#!/bin/bash

#Variables used in this script 
OPENLDAP_PASSWORD="@@{OPENLDAP_PASSWORD}@@"
UID="@@{UID}@@"
SECOND_LEVEL_DOMAIN_NAME="@@{SECOND_LEVEL_DOMAIN_NAME}@@"
TOP_LEVEL_DOMAIN_NAME="@@{TOP_LEVEL_DOMAIN_NAME}@@"
OPENLDAP_PASSWORD="@@{OPENLDAP_PASSWORD}@@"
OBJECT_CLASS="@@{OBJECT_CLASS}@@"
ADD_FIRST_NAME="@@{ADD_FIRST_NAME}@@"
ADD_SECOND_NAME="@@{ADD_SECOND_NAME}@@"
ROLE="@@{ROLE}@@"
PASSWORD="@@{PASSWORD}@@"

echo 'dn: uid=${UID},ou=People,dc=${SECOND_LEVEL_DOMAIN_NAME},dc=${TOP_LEVEL_DOMAIN_NAME}
objectClass: top
objectClass: posixAccount
objectClass: shadowAccount
objectClass: ${OBJECT_CLASS}
cn: ${ADD_FIRST_NAME}
sn: ${ADD_SECOND_NAME}
uid: ${UID}
uidNumber: 9999
gidNumber: 100
homeDirectory: /home/${UID}
loginShell: /bin/bash
gecos: ${ROLE}
userPassword: ${PASSWORD}
shadowLastChange: 17058
shadowMin: 0
shadowMax: 99999
shadowWarning: 7
ou: Group
' | sudo tee ~/${UID}.ldif

/usr/bin/ldapadd -x -w ${OPENLDAP_PASSWORD} -D "cn=ldapadm,dc=${SECOND_LEVEL_DOMAIN_NAME},dc=${TOP_LEVEL_DOMAIN_NAME}" -f ~/${UID}.ldif

sudo /usr/sbin/slaptest -u >> ~/status.txt

# verify the new user was added

ldapsearch -x cn=${UID} -b dc=${SECOND_LEVEL_DOMAIN_NAME},dc=${TOP_LEVEL_DOMAIN_NAME} >> ~/status.txt