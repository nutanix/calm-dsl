#!/bin/bash
set -ex

sudo yum install deltarpm -y
sudo yum install -y --quiet "http://repo.mysql.com/mysql80-community-release-el7.rpm"
sudo yum update -y --quiet
sudo yum install -y --quiet sshpass mysql-community-server

echo "[client]
default-character-set=utf8

[mysql]
default-character-set=utf8

[mysqld]
collation-server = utf8_unicode_ci
character-set-server = utf8
default_authentication_plugin = mysql_native_password" | sudo tee -a /etc/my.cnf

sudo systemctl enable mysqld

if free | awk '/^Swap:/ {exit !$2}'; then
    echo "Swap space exists"
else
    sudo dd if=/dev/zero of=/swapfile bs=1M count=1024
    sudo mkswap /swapfile
    sudo swapon /swapfile
fi

sudo systemctl start mysqld

#Fix to obtain temp password and set it to blank
password=$(sudo grep -oP 'temporary password(.*): \K(\S+)' /var/log/mysqld.log)
sudo mysqladmin --user=root --password="$password" password aaBB**cc1122
sudo mysql --user=root --password=aaBB**cc1122 -e "UNINSTALL COMPONENT 'file://component_validate_password'"
sudo mysqladmin --user=root --password="aaBB**cc1122" password ""

# -*- Mysql secure installation
mysql -u root<<EOF
ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY '@@{MYSQL_PASSWORD}@@';
DELETE FROM mysql.user WHERE User='root' AND Host NOT IN ('localhost', '127.0.0.1', '::1');
DELETE FROM mysql.user WHERE User='';
DELETE FROM mysql.db WHERE Db='test' OR Db='test\_%';
FLUSH PRIVILEGES;
EOF
