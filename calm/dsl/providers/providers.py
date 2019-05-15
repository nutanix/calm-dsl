
VM_PLUGINS = {
    'AHV_VM': 
        ('calm.dsl.providers.ahv.validator', 'AHV_Validator')
}


def get_validator(vm_type):
    
    if vm_type not in VM_PLUGINS:
        raise Exception('provider not found')

    mod_name, validator_name = VM_PLUGINS[vm_type]
    validator_mod = __import__(
            mod_name, globals(), locals(), validator_name
    )
        
    validator_cls = getattr(validator_mod, validator_name)

    return validator_cls