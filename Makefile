NAME    := ntnx/calm-dsl
VERSION := $(shell git describe --abbrev=0 --tags 2>/dev/null || cat CalmVersion)
COMMIT  := $(shell git rev-parse --short HEAD)
TAG     := $(shell git describe --abbrev=0 --tags --exact-match ${COMMIT} 2>/dev/null \
		|| echo ${VERSION}.$(shell date +"%Y.%m.%d").commit.${COMMIT})

dev:
	# Setup our python3 based virtualenv
	# This step assumes python3 is installed on your dev machine
	[ -f venv/bin/python3 ] || (virtualenv -p python3 venv && \
		venv/bin/pip3 install --upgrade pip setuptools)
	venv/bin/pip3 install --use-feature=2020-resolver --no-cache -r requirements.txt -r dev-requirements.txt
	venv/bin/python3 setup.py develop

test: dev
	venv/bin/calm update cache
	venv/bin/py.test -v -rsx --durations 10 -m "not slow" --ignore=examples/

test-all: test
	venv/bin/py.test -v -rsx -m "slow"

gui: dev
	# Setup Jupyter
	venv/bin/pip3 install -r gui-requirements.txt
	venv/bin/jupyter contrib nbextension install --user
	venv/bin/jupyter nbextensions_configurator enable --user
	venv/bin/jupyter nbextension install --py jupyter_dashboards --sys-prefix
	venv/bin/jupyter nbextension enable --py jupyter_dashboards --sys-prefix

clean:
	[ ! -d build/ ] || rm -r build/
	[ ! -d dist/ ] || rm -r dist/
	[ ! -d *.egg-info/ ] || rm -r *.egg-info/
	[ -S /var/run/docker.sock ] && \
		docker ps -aq --no-trunc --filter "status=exited" | xargs -I {} docker rm {} && \
		docker image prune -f
	rm -r venv/ && mkdir venv/ && touch venv/.empty

test-verbose: dev
	venv/bin/py.test -s -vv

dist: dev
	venv/bin/python3 setup.py sdist bdist_wheel

docker: dist

	# Docker doesn't support semver tags + used for metadata info
	# https://github.com/docker/distribution/pull/1202
	# Using commit as pre-release tag

	[ -S /var/run/docker.sock ] && \
		docker build . --rm --file Dockerfile --tag ${NAME}:${TAG} --build-arg tag=${TAG} && \
		docker tag ${NAME}:${TAG} ${NAME}:latest

black:
	black .

run:
	docker run -it ${NAME}

_init_centos:
	# Lets get python3 in
	rpm -q epel-release || sudo yum -y install epel-release openssl-devel
	# Not needed: This has a modern git
	# rpm -q wandisco-git-release || sudo yum install -y http://opensource.wandisco.com/centos/7/git/x86_64/wandisco-git-release-7-2.noarch.rpm || :
	#sudo yum update -y git || :

	sudo yum makecache

	# Install docker
	which docker || { curl -fsSL https://get.docker.com/ | sh; sudo systemctl start docker; sudo systemctl enable docker; sudo usermod -aG docker $(whoami); }

	rpm -q python36 || sudo yum -y install python36 python-pip python3-devel

	# Install virtual env
	sudo pip install -U virtualenv==20.0.18
