from ..providers import get_provider_interface


ProviderInterface = get_provider_interface()


class ExistingMachineProvider(
    ProviderInterface, provider_type="EXISTING_VM", package_name=__name__
):
    """Implements Provider interface for Existing machine"""
    pass
