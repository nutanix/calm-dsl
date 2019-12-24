et -ex

port=5000
sudo yum update -y
sudo yum install -y haproxy

echo "global
  log 127.0.0.1 local0
  log 127.0.0.1 local1 notice
  maxconn 4096
  quiet
  user haproxy
  group haproxy
defaults
  log     global
  mode    http
  retries 3
  timeout client 50s
  timeout connect 5s
  timeout server 50s
  option dontlognull
  option httplog
  option redispatch
  balance  roundrobin
# Set up application listeners here.
listen stats 0.0.0.0:8080
  mode http
  log global
  stats enable
  stats hide-version
  stats refresh 30s
  stats show-node
  stats uri /stats
frontend http
  maxconn 2000
  bind 0.0.0.0:80
  default_backend servers-http
backend servers-http" | sudo tee /etc/haproxy/haproxy.cfg

sudo sed -i 's/server host-/#server host-/g' /etc/haproxy/haproxy.cfg
echo "  server host-@@{WebServer1.address}@@ @@{WebServer1.address}@@:${port} weight 1 maxconn 100 check" | sudo tee -a /etc/haproxy/haproxy.cfg
echo "  server host-@@{WebServer2.address}@@ @@{WebServer2.address}@@:${port} weight 1 maxconn 100 check" | sudo tee -a /etc/haproxy/haproxy.cfg
echo "  server host-@@{WebServerK8sDeploymentPublished_Service.ingress}@@ @@{WebServerK8sDeploymentPublished_Service.ingress}@@:80 weight 1 maxconn 100 check"   | sudo tee -a /etc/haproxy/haproxy.cfg

sudo systemctl daemon-reload
sudo systemctl enable haproxy
sudo systemctl restart haproxy
