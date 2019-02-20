test:
	python3 setup.py develop
	py.test -s --cov -vv

dist: test
	python3 setup.py bdist_wheel

docker: dist
	docker build -t ideadevice/calm-dsl-engine .

clean:
	rm -r build/ dist/ calm.dsl.egg-info/ || echo "No directory found"
	docker image prune -f


_init:
	# Lets get python3 in
	rpm -q epel-release || sudo yum -y install epel-release
	# This has a modern git
	rpm -q wandisco-git-release || sudo yum install -y http://opensource.wandisco.com/centos/7/git/x86_64/wandisco-git-release-7-2.noarch.rpm || :

	sudo yum makecache

	rpm -q python36 || sudo yum -y install python36 python-pip
	sudo yum update -y git

	# Setup our python3 based virtualenv
	[ -f venv/bin/python3 ] || virtualenv -p python36 venv
	venv/bin/pip3 install -U pip setuptools

	venv/bin/pip3 install -r requirements.txt -r dev-requirements.txt

gui: _init
	venv/bin/pip3 install -r gui-requirements.txt
	jupyter contrib nbextension install --user
	jupyter nbextensions_configurator enable --user
