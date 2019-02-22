clean:
	[ ! -d build/ ] || rm -r build/
	[ ! -d dist/ ] || rm -r dist/
	[ ! -d *.egg-info/ ] || rm -r *.egg-info/
	[ -S /var/run/docker.sock ] && \
		docker ps -aq --no-trunc --filter "status=exited" | xargs docker rm && \
		docker image prune -f
	rm -r venv/ && mkdir venv/ && touch venv/.empty

dev:
	# Setup our python3 based virtualenv
	# This step assumes python3 is installed on your dev machine
	[ -f venv/bin/python3 ] || (virtualenv -p python3 venv && \
		venv/bin/pip3 install --upgrade pip setuptools)
	venv/bin/pip3 install -r requirements.txt -r dev-requirements.txt
	venv/bin/python3 setup.py develop

gui: dev
	# Setup Jupyter
	venv/bin/pip3 install -r gui-requirements.txt
	venv/bin/jupyter contrib nbextension install --user
	venv/bin/jupyter nbextensions_configurator enable --user
	venv/bin/jupyter nbextension install --py jupyter_dashboards --sys-prefix
	venv/bin/jupyter nbextension enable --py jupyter_dashboards --sys-prefix


test: dev
	venv/bin/py.test -s --cov -vv

dist: test
	venv/bin/python3 setup.py bdist_wheel

docker: dist gui
	[ -S /var/run/docker.sock ] && \
		docker build --rm -t ideadevice/calm-dsl-engine .

run:
	docker run -it -p 8888:8888 ideadevice/calm-dsl-engine

_init_centos:
	# Lets get python3 in
	rpm -q epel-release || sudo yum -y install epel-release
	# Not needed: This has a modern git
	# rpm -q wandisco-git-release || sudo yum install -y http://opensource.wandisco.com/centos/7/git/x86_64/wandisco-git-release-7-2.noarch.rpm || :
	#sudo yum update -y git || :

	sudo yum makecache

	# Install docker
	which docker || { curl -fsSL https://get.docker.com/ | sh; sudo systemctl start docker; sudo systemctl enable docker; sudo usermod -aG docker $(whoami); }

	rpm -q python36 || sudo yum -y install python36 python-pip
