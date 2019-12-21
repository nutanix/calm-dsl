#!/bin/bash
set -ex
sudo chef-server-ctl user-create @@{CHEF_USERNAME}@@ @@{FIRST_NAME}@@ @@{MIDDLE_NAME}@@ @@{LAST_NAME}@@ @@{EMAIL}@@ @@{CHEF_PASSWORD}@@
sudo chef-server-ctl org-create @@{CHEF_ORG_NAME}@@ '@@{CHEF_ORG_FULL_NAME}@@' --association_user @@{CHEF_USERNAME}@@
