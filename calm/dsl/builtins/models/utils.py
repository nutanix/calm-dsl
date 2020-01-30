import os
import sys
import inspect
from ruamel import yaml
from calm.dsl.tools import get_logging_handle

LOG = get_logging_handle(__name__)


def read_file(filename, depth=1):
    """reads the file"""

    if not filename:
        raise ValueError("filename not supplied")

    file_path = os.path.join(
        os.path.dirname(inspect.getfile(sys._getframe(depth))), filename
    )

    if not os.path.exists(file_path):
        LOG.debug("file {} not found at location {}".format(filename, file_path))
        raise ValueError("file {} not found".format(filename))

    with open(file_path, "r") as data:
        return data.read()


def read_local_file(filename):
    file_path = os.path.join(".local", filename)

    # Checking if file exists
    abs_file_path = os.path.join(
        os.path.dirname(inspect.getfile(sys._getframe(1))), file_path
    )

    # If not exists read from home directory
    if not os.path.exists(abs_file_path):
        file_path = os.path.join(os.path.expanduser("~"), ".calm", ".local", filename)
        return read_file(file_path, 0).rstrip()  # To remove \n, use rstrip

    return read_file(file_path, depth=2)


def str_presenter(dumper, data):
    """For handling multiline strings"""
    if len(data.splitlines()) > 1:  # check for multiline string
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


yaml.add_representer(str, str_presenter)
