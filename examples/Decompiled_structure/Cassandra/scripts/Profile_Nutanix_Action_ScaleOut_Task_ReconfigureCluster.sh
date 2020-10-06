sudo sed -i 's/- seeds:.*$/- seeds: \"@@{calm_array_address}@@\"/g' /etc/cassandra/conf/cassandra.yaml
sudo service cassandra stop
sudo service cassandra start