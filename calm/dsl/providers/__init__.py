from .base import (
    get_provider,
    get_providers,
    get_provider_types,
    get_provider_interface,
)


# TODO Load plugin modules from a config
from .plugins.ahv_vm.main import AhvVmProvider
from .plugins.existing_vm.main import ExistingVmProvider

__all__ = [
    "get_provider",
    "get_providers",
    "get_provider_types",
    "get_provider_interface",
    "AhvVmProvider",
    "ExistingVmProvider",
]
