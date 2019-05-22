from ..providers import get_validator_interface


ValidatorBase = get_validator_interface()


class AhvVmValidator(ValidatorBase, provider_type="AHV_VM", package_name=__name__):
    pass
