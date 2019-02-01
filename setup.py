import setuptools


def read_file(filename):
    with open(filename, "r") as f:
        return f.read()


setuptools.setup(
    name="calm.dsl",
    version="0.0.1",
    author="Nutanix",
    author_email="nucalm@nutanix.com",
    description="Calm DSL for blueprints",
    long_description=read_file("README.md"),
    long_description_content_type="text/markdown",
    url="https://github.com/ideadevice/calm/calm-dsl-engine",
    packages=setuptools.find_namespace_packages(include=['calm.*']),
    namespace_packages=['calm'],
    install_requires=read_file('requirements.txt'),
    tests_require=read_file('dev-requirements.txt'),
    zip_safe=False,
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Mozilla Public License 2.0",
        "Operating System :: OS Independent",
    ],
)
