import os
import sys
import inspect
import json

from ruamel import yaml
import re
from calm.dsl.log import get_logging_handle
from calm.dsl.config import get_context

LOG = get_logging_handle(__name__)


def read_file(filename, depth=1):
    """reads the file"""

    if not filename:
        raise ValueError("filename not supplied")

    # Expanding filename
    filename = os.path.expanduser(filename)
    file_path = os.path.join(
        os.path.dirname(inspect.getfile(sys._getframe(depth))), filename
    )

    if not file_exists(file_path):
        LOG.debug("file {} not found at location {}".format(filename, file_path))
        raise ValueError("file {} not found".format(filename))

    with open(file_path, "r") as data:
        return data.read()


def _get_caller_filepath(filename, depth=2):

    return os.path.abspath(
        os.path.join(os.path.dirname(inspect.getfile(sys._getframe(depth))), filename)
    )


def read_env(relpath=".env"):
    """
    read_env() reads from env file present in blueprint directory.
    If it does not exist, it returns os env present in os.environ.
    Custom env file location can also be given with relpath param.
    relpath will look for file relative to blueprint top-level directory.
    Example: relpath=".env2", relpath="env/dev", etc.

    :param relpath: Blueprint env path starting from blueprint dir. (default: "$BP_DIR/.env")
    :type relpath: str
    :return: env dict containing local & os env
    :rtype: dict
    """

    # Init env
    os_env = dict(os.environ)

    # Get filepath
    filepath = _get_caller_filepath(relpath)

    LOG.debug("Reading env from file: {}".format(filepath))

    # Check if file path exists
    if not os.path.exists(filepath):
        LOG.warning("env file {} not found.".format(filepath))
        return os_env

    # Read env
    with open(filepath, "r") as f:
        content = f.readlines()

    local_env_list = []
    for line in content:
        if not line.startswith("#") and "=" in line:
            # Remove any whitespace characters
            line = line.strip()

            # Get env name & value
            name, value = line.split("=", 1)

            # Remove any extra whitespaces
            name = name.strip()
            value = value.strip()

            # Remove any comments given after value
            value = value.split("#")[0].strip()

            # Remove any quotes in value, if present.
            value = value.strip('"').strip("'")

            local_env_list.append((name, value))

    local_env = dict(local_env_list)
    LOG.debug(
        "Got local env:\n{}".format(
            json.dumps(local_env, indent=4, separators=(",", ": "))
        )
    )

    # Give priority to local env over OS env
    env = {**os_env, **local_env}

    return env


def file_exists(file_path):
    return os.path.exists(file_path)


def read_local_file(filename):
    file_path = os.path.join(".local", filename)

    # Checking if file exists
    abs_file_path = os.path.join(
        os.path.dirname(inspect.getfile(sys._getframe(1))), file_path
    )

    # If not exists read from home directory
    if not file_exists(abs_file_path):
        ContextObj = get_context()
        init_data = ContextObj.get_init_config()
        file_path = os.path.join(init_data["LOCAL_DIR"]["location"], filename)
        return read_file(file_path, 0).rstrip()  # To remove \n, use rstrip

    return read_file(file_path, depth=2)


def str_presenter(dumper, data):
    """For handling multiline strings"""
    if len(data.splitlines()) > 1:  # check for multiline string
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


yaml.add_representer(str, str_presenter)


def get_valid_identifier(data=None):
    """returns a valid indentifier out of string"""

    if not data:
        return data

    if data.isidentifier():
        return data

    # Will remove all unwanted characters
    data = re.sub("[^0-9a-zA-Z_]", "", data)

    # Still it is an invalid indentifier, it will append "_" i.e underscore at start
    if not data.isidentifier():
        data = "_{}".format(data)

    return data
