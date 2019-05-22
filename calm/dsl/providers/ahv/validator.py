from ..providers import get_validator_interface


ValidatorBase = get_validator_interface()


class AhvVmValidator(ValidatorBase, provider_type="AHV_VM"):

    def __init__(self):
        super().__init__(__name__)
