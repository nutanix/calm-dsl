from ..providers import get_validator_interface


ValidatorBase = get_validator_interface()


class ExistingMachineValidator(
    ValidatorBase, provider_type="EXISTING_VM", package_name=__name__
):
    pass
