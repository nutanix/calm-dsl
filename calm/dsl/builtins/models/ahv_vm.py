from .entity import EntityType, Entity
from .validator import PropertyValidator
from .ahv_vm_disk import get_boot_config
from .provider_spec import ProviderSpecType

# AHV VM Resources


class AhvVmResourcesType(EntityType):
    __schema_name__ = "AhvVmResources"
    __openapi_type__ = "vm_ahv_resources"

    def compile(cls):
        cdict = super().compile()

        cdict["boot_config"] = get_boot_config()

        # Converting memory from GiB to mib
        cdict["memory_size_mib"] *= 1024

        # Merging boot_type to boot_config
        boot_type = cdict.pop("boot_type")
        if boot_type == "UEFI":
            cdict["boot_config"]["boot_type"] = "UEFI"

        serial_port_list = []
        for ind, connection_status in cdict["serial_port_list"].items():
            if not isinstance(ind, int):
                raise TypeError("index {} is not of type integer".format(ind))

            if not isinstance(connection_status, bool):
                raise TypeError(
                    "connection status {} is not of type bool".format(connection_status)
                )

            serial_port_list.append({"index": ind, "is_connected": connection_status})

        cdict["serial_port_list"] = serial_port_list

        return cdict


class AhvVmResourcesValidator(PropertyValidator, openapi_type="vm_ahv_resources"):
    __default__ = None
    __kind__ = AhvVmResourcesType


def ahv_vm_resources(**kwargs):
    name = kwargs.get("name", None)
    bases = (Entity,)
    return AhvVmResourcesType(name, bases, kwargs)


AhvVmResources = ahv_vm_resources()


# AHV VM


class AhvVmType(ProviderSpecType):
    __schema_name__ = "AhvVm"
    __openapi_type__ = "vm_ahv"


class AhvVmValidator(PropertyValidator, openapi_type="vm_ahv"):
    __default__ = None
    __kind__ = AhvVmType


def ahv_vm(**kwargs):
    name = kwargs.get("name", None)
    bases = (Entity,)
    return AhvVmType(name, bases, kwargs)


AhvVm = ahv_vm()
