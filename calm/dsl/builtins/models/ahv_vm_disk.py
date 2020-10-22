import sys

from .entity import EntityType, Entity
from .validator import PropertyValidator
from .ref import ref

from .package import PackageType
from .metadata_payload import get_metadata_obj
from calm.dsl.store import Cache
from calm.dsl.config import get_context
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)

# AHV VM Disk


IMAGE_TYPE_MAP = {"DISK": "DISK_IMAGE", "CDROM": "ISO_IMAGE"}


class AhvDiskType(EntityType):
    __schema_name__ = "AhvDisk"
    __openapi_type__ = "vm_ahv_disk"

    def compile(cls):
        cdict = super().compile()
        # Pop bootable from cdict
        cdict.pop("bootable", None)

        # Getting the metadata obj
        metadata_obj = get_metadata_obj()
        project_ref = metadata_obj.get("project_reference") or dict()

        # If project not found in metadata, it will take project from config
        context = get_context()
        project_config = context.get_project_config()
        project_name = project_ref.get("name") or project_config["name"]

        project_cache_data = Cache.get_entity_data(
            entity_type="project", name=project_name
        )
        if not project_cache_data:
            LOG.error(
                "Project {} not found. Please run: calm update cache".format(
                    project_name
                )
            )
            sys.exit(-1)

        # Fetch Nutanix_PC account registered
        project_accounts = project_cache_data["accounts_data"]
        account_uuid = project_accounts.get("nutanix_pc", "")

        if not account_uuid:
            LOG.error(
                "No nutanix account registered to project {}".format(project_name)
            )
            sys.exit(-1)

        image_ref = cdict.get("data_source_reference") or dict()
        if image_ref and image_ref["kind"] == "image":
            image_name = image_ref.get("name")
            device_type = cdict["device_properties"].get("device_type")

            image_cache_data = Cache.get_entity_data(
                entity_type="ahv_disk_image",
                name=image_name,
                image_type=IMAGE_TYPE_MAP[device_type],
                account_uuid=account_uuid,
            )
            if not image_cache_data:
                LOG.debug(
                    "Ahv Disk Image (name = '{}') not found in registered nutanix_pc account (uuid = '{}') in project (name = '{}')".format(
                        image_name, account_uuid, project_name
                    )
                )
                LOG.error(
                    "Ahv Disk Image {} not found. Please run: calm update cache".format(
                        image_name
                    )
                )
                sys.exit(-1)

            image_uuid = image_cache_data.get("uuid", "")
            cdict["data_source_reference"] = {
                "kind": "image",
                "name": image_name,
                "uuid": image_uuid,
            }

        return cdict


class AhvDiskValidator(PropertyValidator, openapi_type="vm_ahv_disk"):
    __default__ = None
    __kind__ = AhvDiskType


def ahv_vm_disk(**kwargs):
    name = kwargs.get("name", None)
    bases = (Entity,)
    return AhvDiskType(name, bases, kwargs)


def allocate_on_storage_container(adapter_type="SCSI", size=8):
    kwargs = {
        "device_properties": {
            "device_type": "DISK",
            "disk_address": {"adapter_type": adapter_type, "device_index": -1},
        },
        "disk_size_mib": size * 1024,
    }

    return ahv_vm_disk(**kwargs)


def update_disk_config(
    device_type="DISK", adapter_type="SCSI", image_data={}, bootable=False
):
    if not image_data:
        raise ValueError("Image data not found")

    kwargs = {
        "data_source_reference": image_data,
        "device_properties": {
            "device_type": device_type,
            "disk_address": {"adapter_type": adapter_type, "device_index": -1},
        },
        "disk_size_mib": 0,
        "bootable": bootable,
    }

    return ahv_vm_disk(**kwargs)


def clone_from_image_service(
    device_type="DISK", adapter_type="SCSI", image_name="", bootable=False
):

    if not image_name:
        LOG.error("image_name not provided")
        sys.exit(-1)

    # image_uuid will be added at compile time as it requires project context
    image_data = {"kind": "image", "name": image_name}

    return update_disk_config(device_type, adapter_type, image_data, bootable)


def clone_from_vm_image_service(
    device_type="DISK", adapter_type="SCSI", bootable=False, vm_disk_package=None
):
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
    kwargs = {
        "device_properties": {
            "device_type": "CDROM",
            "disk_address": {"adapter_type": adapter_type, "device_index": -1},
        },
        "disk_size_mib": 0,
    }

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
