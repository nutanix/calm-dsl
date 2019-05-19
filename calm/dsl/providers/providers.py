
class Validator_Base(object):

    validators = {}

    def __init_subclass__(cls, vm_type, **kwargs):
        super().__init_subclass__(**kwargs)

        if vm_type is not None:

            cls.validators[vm_type] = cls


def get_validator(vm_type):

    if vm_type not in Validator_Base.validators:
        raise Exception('provider not registered')
    
    return Validator_Base.validators[vm_type]
