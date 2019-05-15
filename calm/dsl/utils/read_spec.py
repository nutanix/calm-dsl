import os
import sys
import inspect
from ruamel import yaml
from calm.dsl.providers import get_validator


def read_ahv_vm_spec(filename):

    file_path = os.path.join(
        os.path.dirname(inspect.getfile(sys._getframe(1))), filename
    )

    with open(file_path, "r") as f:
        return yaml.safe_load(f.read())


class CreateSpecReader:

    def __init__(self, create_spec):

        self.create_spec = create_spec
    
    def __validate__(self, vm_type):

        validator_cls = get_validator(vm_type)
        validator = validator_cls()
        validator.validate(self.create_spec)

        return self.create_spec

    def __get__(self, instance, cls):

        if cls is None:
            return self

        vm_type = cls.type
        return self.__validate__(vm_type)


def read_vm_spec(filename):

    file_path = os.path.join(
        os.path.dirname(
            inspect.getfile(
                sys._getframe(1))),
        filename)

    with open(file_path, "r") as f:
        create_spec = yaml.safe_load(f.read())

    return CreateSpecReader(create_spec)
