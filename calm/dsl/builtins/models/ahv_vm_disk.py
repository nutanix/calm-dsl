from .ahv_vm import ahv_vm_disk


# AHV Disk

ADAPTER_INDEX_MAP = {"SCSI": 0, "PCI": 0, "IDE": 0, "SATA": 0}
BOOT_CONFIG = {}


def get_boot_config():
    if not BOOT_CONFIG:
        raise ValueError("There is no bootable disk selected.")

    return BOOT_CONFIG


def allocate_disk_on_storage_container(device_type="DISK", adapter_type="SCSI", size=8):
    global ADAPTER_INDEX_MAP
    kwargs = {
        "data_source_reference": None,  # Must be there
        "device_properties": {
            "device_type": device_type,
            "disk_address": {
                "adapter_type": adapter_type,
                "device_index": ADAPTER_INDEX_MAP[adapter_type],
            },
        },
        "disk_size_mib": size * 1024,
    }

    ADAPTER_INDEX_MAP[adapter_type] += 1
    return ahv_vm_disk(**kwargs)


def clone_disk_from_image_service(
    device_type="DISK", adapter_type="SCSI", image_name="", bootable=False
):
    global ADAPTER_INDEX_MAP

    if not image_name:
        raise ValueError("image name not supplied !!!")
    kwargs = {
        "data_source_reference": {"kind": "image", "name": image_name},  # TODO add UUID
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
                        "device_type": adapter_type,
                    }
                }
            }
        )

    ADAPTER_INDEX_MAP[adapter_type] += 1
    return ahv_vm_disk(**kwargs)


def disk_scsi_clone_from_image(image_name=None, bootable=False):
    return clone_disk_from_image_service(
        device_type="DISK",
        adapter_type="SCSI",
        image_name=image_name,
        bootable=bootable,
    )


def disk_pci_clone_from_image(image_name=None, bootable=False):
    return clone_disk_from_image_service(
        device_type="DISK", adapter_type="PCI", image_name=image_name, bootable=bootable
    )


def cd_rom_ide_clone_from_image(image_name=None, bootable=False):
    return clone_disk_from_image_service(
        device_type="CD-ROM",
        adapter_type="IDE",
        image_name=image_name,
        bootable=bootable,
    )


def cd_rom_sata_clone_from_image(image_name=None, bootable=False):
    return clone_disk_from_image_service(
        device_type="CD-ROM",
        adapter_type="SATA",
        image_name=image_name,
        bootable=bootable,
    )


def disk_scsi_allocate_on_container(size=8):
    return allocate_disk_on_storage_container(
        device_type="DISK", adapter_type="SCSI", size=size
    )


def disk_pci_allocate_on_container(size=8):
    return allocate_disk_on_storage_container(
        device_type="DISK", adapter_type="PCI", size=size
    )


def cd_rom_ide_allocate_on_container(size=8):
    return allocate_disk_on_storage_container(
        device_type="CD-ROM", adapter_type="IDE", size=size
    )


def cd_rom_sata_allocate_on_container(size=8):
    return allocate_disk_on_storage_container(
        device_type="CD-ROM", adapter_type="SATA", size=size
    )


class AhvVmDisk:
    def __new__(cls, image_name=None, bootable=False):
        return disk_scsi_clone_from_image(image_name=image_name, bootable=False)

    class Disk:
        def __new__(cls, image_name=None, bootable=False):
            return disk_scsi_clone_from_image(image_name=image_name, bootable=False)

        class Scsi:
            def __new__(cls, image_name=None, bootable=False):
                return disk_scsi_clone_from_image(image_name=image_name, bootable=False)

            cloneFromImageService = disk_scsi_clone_from_image
            allocateOnStorageContainer = disk_scsi_allocate_on_container

        class Pci:
            def __new__(cls, image_name=None, bootable=False):
                return disk_pci_clone_from_image(image_name=image_name, bootable=False)

            cloneFromImageService = disk_pci_clone_from_image
            allocateOnStorageContainer = disk_pci_allocate_on_container

    class CdRom:
        def __new__(cls, image_name=None, bootable=False):
            return cd_rom_ide_clone_from_image(image_name=image_name, bootable=False)

        class Ide:
            def __new__(cls, image_name=None, bootable=False):
                return cd_rom_ide_clone_from_image(
                    image_name=image_name, bootable=False
                )

            cloneFromImageService = cd_rom_ide_clone_from_image
            allocateOnStorageContainer = cd_rom_ide_clone_from_image

        class Sata:
            def __new__(cls, image_name=None, bootable=False):
                return cd_rom_sata_clone_from_image(
                    image_name=image_name, bootable=False
                )

            cloneFromImageService = cd_rom_sata_clone_from_image
            allocateOnStorageContainer = cd_rom_sata_allocate_on_container
