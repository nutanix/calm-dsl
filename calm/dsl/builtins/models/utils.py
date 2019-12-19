import os
import sys
import inspect
from ruamel import yaml


def read_file(filename, depth=1):
    """reads the file"""

    if not filename:
        raise ValueError("filename not supplied")

    file_path = os.path.join(
        os.path.dirname(inspect.getfile(sys._getframe(depth))), filename
    )

    if not os.path.exists(file_path):
        raise ValueError("file {} not found".format(filename))

    with open(file_path, "r") as data:
        return data.read()


def read_local_file(filename):
    filename = ".local/" + filename
    # TODO - Add support to read from user local dir ~/.calm/.local/ if not present here
    return read_file(filename, depth=2)


def str_presenter(dumper, data):
    """For handling multiline strings"""
    if len(data.splitlines()) > 1:  # check for multiline string
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


yaml.add_representer(str, str_presenter)
