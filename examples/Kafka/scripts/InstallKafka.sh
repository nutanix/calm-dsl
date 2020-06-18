sudo wget "@@{KAFKA_URL}@@" -O /opt/kafka.tgz
cd /opt/
sudo chmod a+x kafka.tgz
sudo mkdir -p kafka
sudo tar -xzf kafka.tgz -C kafka/
sudo mv /opt/kafka/kafka_*/* /opt/kafka/
