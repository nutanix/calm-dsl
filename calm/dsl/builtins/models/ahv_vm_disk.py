from .entity import EntityType, Entity
from .validator import PropertyValidator
from calm.dsl.store import Cache
from .ref import ref
from .package import PackageType


# AHV VM Disk


ADAPTER_INDEX_MAP = {"SCSI": 0, "PCI": 0, "IDE": 0, "SATA": 0}
BOOT_CONFIG = {}


class AhvDiskType(EntityType):
    __schema_name__ = "AhvDisk"
    __openapi_type__ = "vm_ahv_disk"


class AhvDiskValidator(PropertyValidator, openapi_type="vm_ahv_disk"):
    __default__ = None
    __kind__ = AhvDiskType


def ahv_vm_disk(**kwargs):
    name = kwargs.get("name", None)
    bases = (Entity,)
    return AhvDiskType(name, bases, kwargs)


def get_boot_config():
    if not BOOT_CONFIG:
        raise ValueError("There is no bootable disk selected.")

    return BOOT_CONFIG


def allocate_on_storage_container(adapter_type="SCSI", size=8):
    global ADAPTER_INDEX_MAP
    kwargs = {
        "device_properties": {
            "device_type": "DISK",
            "disk_address": {
                "adapter_type": adapter_type,
                "device_index": ADAPTER_INDEX_MAP[adapter_type],
            },
        },
        "disk_size_mib": size * 1024,
    }

    ADAPTER_INDEX_MAP[adapter_type] += 1
    return ahv_vm_disk(**kwargs)


def update_disk_config(
    device_type="DISK", adapter_type="SCSI", image_data={}, bootable=False
):
    if not image_data:
        raise ValueError("Image data not found")

    global ADAPTER_INDEX_MAP
    kwargs = {
        "data_source_reference": image_data,
        "device_properties": {
            "device_type": device_type,
            "disk_address": {
                "adapter_type": adapter_type,
                "device_index": ADAPTER_INDEX_MAP[adapter_type],
            },
        },
        "disk_size_mib": 0,
    }

    if bootable:
        global BOOT_CONFIG
        BOOT_CONFIG.update(
            {
                "boot_device": {
                    "disk_address": {
                        "device_index": ADAPTER_INDEX_MAP[adapter_type],
                        "adapter_type": adapter_type,
                    }
                }
            }
        )

    ADAPTER_INDEX_MAP[adapter_type] += 1
    return ahv_vm_disk(**kwargs)


def clone_from_image_service(
    device_type="DISK", adapter_type="SCSI", image_name="", bootable=False
):
    if not image_name:
        raise ValueError("image_name not provided !!!")

    image_uuid = Cache.get_entity_uuid("AHV_DISK_IMAGE", image_name)
    if not image_uuid:
        raise Exception(
            "Ahv Disk Image {} not found. Please run: calm update cache".format(
                image_name
            )
        )

    image_data = {"kind": "image", "name": image_name, "uuid": image_uuid}

    return update_disk_config(device_type, adapter_type, image_data, bootable)


def clone_from_vm_image_service(
    device_type="DISK", adapter_type="SCSI", bootable=False, vm_disk_package=None
):
    global ADAPTER_INDEX_MAP

    if not vm_disk_package:
        raise ValueError("vm_disk_package not provided !!!")

    if not isinstance(vm_disk_package, PackageType):
        raise TypeError("{} is not of type {}".format(vm_disk_package, PackageType))

    AHV_IMAGE_TYPES = {"DISK": "DISK_IMAGE", "CDROM": "ISO_IMAGE"}
    pkg = vm_disk_package.compile()
    vm_image_type = pkg["options"]["resources"]["image_type"]

    if vm_image_type != AHV_IMAGE_TYPES[device_type]:
        raise ValueError("Invalid vm image {} supplied in disk".format(vm_disk_package))

    image_data = ref(vm_disk_package).compile()

    return update_disk_config(device_type, adapter_type, image_data, bootable)


def empty_cd_rom(adapter_type="IDE"):
    global ADAPTER_INDEX_MAP
    kwargs = {
        "device_properties": {
            "device_type": "CDROM",
            "disk_address": {
                "adapter_type": adapter_type,
                "device_index": ADAPTER_INDEX_MAP[adapter_type],
            },
        },
        "disk_size_mib": 0,
    }

    ADAPTER_INDEX_MAP[adapter_type] += 1
    return ahv_vm_disk(**kwargs)


def disk_scsi_clone_from_image(image_name=None, bootable=False):
    return clone_from_image_service(
        device_type="DISK",
        adapter_type="SCSI",
        image_name=image_name,
        bootable=bootable,
    )


def disk_pci_clone_from_image(image_name=None, bootable=False):
    return clone_from_image_service(
        device_type="DISK", adapter_type="PCI", image_name=image_name, bootable=bootable
    )


def cd_rom_ide_clone_from_image(image_name=None, bootable=False):
    return clone_from_image_service(
        device_type="CDROM",
        adapter_type="IDE",
        image_name=image_name,
        bootable=bootable,
    )


def cd_rom_sata_clone_from_image(image_name=None, bootable=False):
    return clone_from_image_service(
        device_type="CDROM",
        adapter_type="SATA",
        image_name=image_name,
        bootable=bootable,
    )


def disk_scsi_clone_from_pkg_image(vm_disk_package=None, bootable=False):
    return clone_from_vm_image_service(
        device_type="DISK",
        adapter_type="SCSI",
        vm_disk_package=vm_disk_package,
        bootable=bootable,
    )


def disk_pci_clone_from_pkg_image(vm_disk_package=None, bootable=False):
    return clone_from_vm_image_service(
        device_type="DISK",
        adapter_type="PCI",
        vm_disk_package=vm_disk_package,
        bootable=bootable,
    )


def cd_rom_ide_clone_from_pkg_image(vm_disk_package=None, bootable=False):
    return clone_from_vm_image_service(
        device_type="CDROM",
        adapter_type="IDE",
        vm_disk_package=vm_disk_package,
        bootable=bootable,
    )


def cd_rom_sata_clone_from_pkg_image(vm_disk_package=None, bootable=False):
    return clone_from_vm_image_service(
        device_type="CDROM",
        adapter_type="SATA",
        vm_disk_package=vm_disk_package,
        bootable=bootable,
    )


def disk_scsi_allocate_on_container(size=8):
    return allocate_on_storage_container(adapter_type="SCSI", size=size)


def disk_pci_allocate_on_container(size=8):
    return allocate_on_storage_container(adapter_type="PCI", size=size)


def cd_rom_ide_use_empty_cd_rom():
    return empty_cd_rom(adapter_type="IDE")


def cd_rom_sata_use_empty_cd_rom():
    return empty_cd_rom(adapter_type="SATA")


class AhvVmDisk:
    def __new__(cls, image_name=None, bootable=False):
        return disk_scsi_clone_from_image(image_name=image_name, bootable=bootable)

    class Disk:
        def __new__(cls, image_name=None, bootable=False):
            return disk_scsi_clone_from_image(image_name=image_name, bootable=bootable)

        class Scsi:
            def __new__(cls, image_name=None, bootable=False):
                return disk_scsi_clone_from_image(
                    image_name=image_name, bootable=bootable
                )

            cloneFromImageService = disk_scsi_clone_from_image
            allocateOnStorageContainer = disk_scsi_allocate_on_container
            cloneFromVMDiskPackage = disk_scsi_clone_from_pkg_image

        class Pci:
            def __new__(cls, image_name=None, bootable=False):
                return disk_pci_clone_from_image(
                    image_name=image_name, bootable=bootable
                )

            cloneFromImageService = disk_pci_clone_from_image
            allocateOnStorageContainer = disk_pci_allocate_on_container
            cloneFromVMDiskPackage = disk_pci_clone_from_pkg_image

    class CdRom:
        def __new__(cls, image_name=None, bootable=False):
            return cd_rom_ide_clone_from_image(image_name=image_name, bootable=bootable)

        class Ide:
            def __new__(cls, image_name=None, bootable=False):
                return cd_rom_ide_clone_from_image(
                    image_name=image_name, bootable=bootable
                )

            cloneFromImageService = cd_rom_ide_clone_from_image
            emptyCdRom = cd_rom_ide_use_empty_cd_rom
            cloneFromVMDiskPackage = cd_rom_ide_clone_from_pkg_image

        class Sata:
            def __new__(cls, image_name=None, bootable=False):
                return cd_rom_sata_clone_from_image(
                    image_name=image_name, bootable=bootable
                )

            cloneFromImageService = cd_rom_sata_clone_from_image
            emptyCdRom = cd_rom_sata_use_empty_cd_rom
            cloneFromVMDiskPackage = cd_rom_sata_clone_from_pkg_image
