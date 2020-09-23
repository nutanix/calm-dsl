import sys
import setuptools
from setuptools.command.test import test as TestCommand


def read_file(filename):
    with open(filename, "r") as f:
        return f.read()


class PyTest(TestCommand):
    """PyTest"""

    def finalize_options(self):
        """finalize_options"""
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        """run_tests"""
        import pytest

        errcode = pytest.main(self.test_args)
        sys.exit(errcode)


setuptools.setup(
    name="calm.dsl",
    version=read_file("CalmVersion"),
    author="Nutanix",
    author_email="nucalm@nutanix.com",
    description="Calm DSL for blueprints",
    long_description=read_file("README.md"),
    long_description_content_type="text/markdown",
    url="https://nutanix.github.io/calm-dsl/",
    packages=setuptools.find_namespace_packages(include=["calm.*"]),
    namespace_packages=["calm"],
    install_requires=read_file("requirements.txt"),
    tests_require=read_file("dev-requirements.txt"),
    cmdclass={"test": PyTest},
    zip_safe=False,
    include_package_data=True,
    entry_points={"console_scripts": ["calm=calm.dsl.cli:main"]},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.7",
    ],
)
