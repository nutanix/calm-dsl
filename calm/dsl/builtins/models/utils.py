import os
import sys
import inspect
from ruamel import yaml


def read_file(filename, depth=1):
    """reads the file"""

    file_path = os.path.join(
        os.path.dirname(inspect.getfile(sys._getframe(depth))), filename
    )

    with open(file_path, "r") as data:
        return data.read()


def str_presenter(dumper, data):
    """For handling multiline strings"""
    if len(data.splitlines()) > 1:  # check for multiline string
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)


yaml.add_representer(str, str_presenter)
