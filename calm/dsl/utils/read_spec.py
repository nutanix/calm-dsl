import os
import sys
import inspect
from ruamel import yaml


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

        Providers = {
            'AHV_VM': 
            ('calm.dsl.builtins.models.create_spec_validator', 'AHV_Validator')
        }

        if vm_type not in Providers:
            raise Exception('given provider : %r is not supported' % (vm_type) )
        
        mod_name, validator_name = Providers[vm_type]  
        validator_mod = __import__(
            mod_name, globals(), locals(), validator_name
        )
        
        validator_cls = getattr(validator_mod, validator_name)
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
