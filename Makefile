test:
	python3 setup.py develop
	python3 tests/single_vm_example/main.py

dist: test
	python3 setup.py sdist bdist_wheel

clean:
	rm -r build/ dist/ calm.dsl.egg-info/

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
