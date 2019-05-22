from ..providers import get_provider_interface


ProviderInterface = get_provider_interface()


class AhvVmProvider(ProviderInterface, provider_type="AHV_VM", package_name=__name__):
    """Implements Provider Interface for AHV VM"""
    pass
