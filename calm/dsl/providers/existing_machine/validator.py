from ..providers import get_validator_interface


ValidatorBase = get_validator_interface()


class ExistingMachineValidator(ValidatorBase, provider_type="EXISTING_VM"):

    def __init__(self):
        super().__init__(__name__)
