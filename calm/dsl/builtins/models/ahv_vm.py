from .entity import EntityType, Entity
from .validator import PropertyValidator
from .provider_spec import ProviderSpecType

# AHV VM Resources


class AhvVmResourcesType(EntityType):
    __schema_name__ = "AhvVmResources"
    __openapi_type__ = "vm_ahv_resources"

    def compile(cls):
        cdict = super().compile()

        ADAPTER_INDEX_MAP = {"SCSI": 0, "PCI": 0, "IDE": 0, "SATA": 0}

        # Traverse over disks and modify the adapter index in disk address
        # Get boot config from disks also
        boot_config = {}
        disk_list = cdict.get("disk_list", [])
        for disk in disk_list:
            disk_data = disk.get_dict()
            device_prop = disk_data["device_properties"]
            adapter_type = device_prop["disk_address"]["adapter_type"]

            device_prop["disk_address"]["device_index"] = ADAPTER_INDEX_MAP[
                adapter_type
            ]
            ADAPTER_INDEX_MAP[adapter_type] += 1
            disk.device_properties = device_prop

            if disk.bootable and not boot_config:
                boot_config = {
                    "boot_device": {"disk_address": device_prop["disk_address"]}
                }

            elif disk.bootable and boot_config:
                raise ValueError("More than one bootable disks found")

        # Converting memory from GiB to mib
        cdict["memory_size_mib"] *= 1024

        # Merging boot_type to boot_config
        cdict["boot_config"] = boot_config
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

    @classmethod
    def decompile(mcls, cdict, context=[]):
        # Check for serial ports
        serial_port_list = cdict.pop("serial_port_list", [])
        serial_port_dict = {}
        for sp in serial_port_list:
            serial_port_dict[sp["index"]] = sp["is_connected"]

        cdict["serial_port_list"] = serial_port_dict

        if not cdict.get("guest_customization", None):
            cdict.pop("guest_customization", None)

        return super().decompile(cdict)


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
