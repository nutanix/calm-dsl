test:
	python3 setup.py develop
	python3 tests/single_vm_example/main.py

dist: test
	python3 setup.py sdist bdist_wheel

clean:
	rm -r build/ dist/ calm.dsl.egg-info/
