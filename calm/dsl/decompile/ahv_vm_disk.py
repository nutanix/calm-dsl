import sys

from calm.dsl.decompile.render import render_template
from calm.dsl.store import Cache
from calm.dsl.log import get_logging_handle

LOG = get_logging_handle(__name__)


def render_ahv_vm_disk(cls, boot_config):

    data_source_ref = cls.data_source_reference or {}
    if data_source_ref:
        data_source_ref = data_source_ref.get_dict()

    device_properties = cls.device_properties.get_dict()

    disk_size_mib = cls.disk_size_mib

    # find device type
    device_type = device_properties["device_type"]
    adapter_type = device_properties["disk_address"]["adapter_type"]
    adapter_index = device_properties["disk_address"]["device_index"]

    schema_file = ""
    user_attrs = {}

    # Atleast one disk should be bootable
    if (
        adapter_type == boot_config["boot_device"]["disk_address"]["adapter_type"]
        and adapter_index == boot_config["boot_device"]["disk_address"]["device_index"]
    ):
        user_attrs["bootable"] = True

    # find operation_type
    if data_source_ref:
        if data_source_ref["kind"] == "app_package":
            user_attrs["name"] = data_source_ref.get("name")
            operation_type = "cloneFromVMDiskPackage"

        elif data_source_ref["kind"] == "image":
            operation_type = "cloneFromImageService"
            img_uuid = data_source_ref.get("uuid")
            disk_cache_data = (
                Cache.get_entity_data_using_uuid(
                    entity_type="ahv_disk_image", uuid=img_uuid
                )
                or {}
            )
            if not disk_cache_data:
                # Windows images may not be present
                LOG.warning("Image with uuid '{}' not found".format(img_uuid))
            user_attrs["name"] = disk_cache_data.get("name", "")

        else:
            LOG.error(
                "Unknown kind `{}` for data source reference in image".format(
                    data_source_ref["kind"]
                )
            )

    else:
        if device_type == "DISK":
            user_attrs["size"] = disk_size_mib // 1024
            operation_type = "allocateOnStorageContainer"

        elif device_type == "CDROM":
            operation_type = "emptyCdRom"

        else:
            LOG.error("Unknown device type")
            sys.exit(-1)

    # TODO add whitelisting from  project via attached accounts
    if device_type == "DISK":
        if adapter_type == "SCSI":
            if operation_type == "cloneFromImageService":
                schema_file = "ahv_vm_disk_scsi_clone_from_image.py.jinja2"

            elif operation_type == "cloneFromVMDiskPackage":
                schema_file = "ahv_vm_disk_scsi_clone_from_pkg.py.jinja2"

            elif operation_type == "allocateOnStorageContainer":
                schema_file = "ahv_vm_disk_scsi_allocate_container.py.jinja2"

            else:
                LOG.error("Unknown operation type {}".format(operation_type))
                sys.exit(-1)

        elif adapter_type == "PCI":
            if operation_type == "cloneFromImageService":
                schema_file = "ahv_vm_disk_pci_clone_from_image.py.jinja2"

            elif operation_type == "cloneFromVMDiskPackage":
                schema_file = "ahv_vm_disk_pci_clone_from_pkg.py.jinja2"

            elif operation_type == "allocateOnStorageContainer":
                schema_file = "ahv_vm_disk_pci_allocate_container.py.jinja2"

            else:
                LOG.error("Unknown operation type {}".format(operation_type))
                sys.exit(-1)

        else:
            LOG.error("Unknown adapter type {}".format(adapter_type))
            sys.exit(-1)

    else:  # CD-ROM
        if adapter_type == "SATA":
            if operation_type == "cloneFromImageService":
                schema_file = "ahv_vm_cdrom_sata_clone_from_image.py.jinja2"

            elif operation_type == "cloneFromVMDiskPackage":
                schema_file = "ahv_vm_cdrom_sata_clone_from_pkg.py.jinja2"

            elif operation_type == "emptyCdRom":
                schema_file = "ahv_vm_cdrom_sata_empty_cdrom.py.jinja2"

            else:
                LOG.error("Unknown operation type {}".format(operation_type))
                sys.exit(-1)

        elif adapter_type == "IDE":
            if operation_type == "cloneFromImageService":
                schema_file = "ahv_vm_cdrom_ide_clone_from_image.py.jinja2"

            elif operation_type == "cloneFromVMDiskPackage":
                schema_file = "ahv_vm_cdrom_ide_clone_from_pkg.py.jinja2"

            elif operation_type == "emptyCdRom":
                schema_file = "ahv_vm_cdrom_ide_empty_cdrom.py.jinja2"

            else:
                LOG.error("Unknown operation type {}".format(operation_type))
                sys.exit(-1)

        else:
            LOG.error("Unknown adapter type {}".format(adapter_type))
            sys.exit(-1)

    text = render_template(schema_file=schema_file, obj=user_attrs)
    return text.strip()
