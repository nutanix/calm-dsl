from .entity import EntityType, Entity
from .validator import PropertyValidator
from .ahv_vm_disk import get_boot_config


# AHV VM Resources


class AhvVmResourcesType(EntityType):
    __schema_name__ = "AhvVmResources"
    __openapi_type__ = "vm_ahv_resources"

    def compile(cls):
        cdict = super().compile()

        # Merging boot_type to boot_config
        boot_type = cdict.pop("boot_type")

        cdict["boot_config"] = get_boot_config()

        if boot_type == "UEFI":
            cdict["boot_config"]["boot_type"] = "UEFI"

        serial_port_list = []
        for ind, connection_status in cdict["serial_port_list"].items():
            serial_port_list.append({"index": ind, "is_connected": connection_status})

        cdict["serial_port_list"] = serial_port_list

        return cdict


class AhvVmResourcesValidator(PropertyValidator, openapi_type="vm_ahv_resources"):
    __default__ = None
    __kind__ = AhvVmResourcesType


def ahv_vm_resources(**kwargs):
    name = getattr(AhvVmResourcesType, "__schema_name__")
    bases = (Entity,)
    return AhvVmResourcesType(name, bases, kwargs)


AhvVmResources = ahv_vm_resources()


# AHV VM


class AhvVmType(EntityType):
    __schema_name__ = "AhvVm"
    __openapi_type__ = "vm_ahv"


class AhvVmValidator(PropertyValidator, openapi_type="vm_ahv"):
    __default__ = None
    __kind__ = AhvVmType


def ahv_vm(**kwargs):
    name = getattr(AhvVmType, "__schema_name__")
    bases = (Entity,)
    return AhvVmType(name, bases, kwargs)


AhvVm = ahv_vm()
