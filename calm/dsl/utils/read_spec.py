import os
import sys
import inspect
from ruamel import yaml


def read_ahv_vm_spec(filename):

    file_path = os.path.join(
        os.path.dirname(
            inspect.getfile(
                sys._getframe(1))),
        filename)

    with open(file_path, "r") as f:
        return yaml.safe_load(f.read())
