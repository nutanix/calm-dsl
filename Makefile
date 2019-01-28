test:
	python3 setup.py develop
	python3 tests/single_vm_example/main.py

dist: test
	python3 setup.py sdist bdist_wheel

clean:
	rm -r build/ dist/ calm.dsl.egg-info/

_init:
	rpm -q epel-release || sudo yum -y install epel-release
	rpm -q python36 || sudo yum -y install python36 python-pip
	[ -f venv/bin/python3 ] || virtualenv -p python36 venv
	venv/bin/pip3 install -U pip setuptools
