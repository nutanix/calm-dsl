import sys

from calm.dsl.decompile.render import render_template
from calm.dsl.store import Cache
from calm.dsl.tools import get_logging_handle

LOG = get_logging_handle(__name__)


def render_ahv_vm_disk(cls):

    data_source_ref = cls.data_source_reference or {}
    if data_source_ref:
        data_source_ref = data_source_ref.get_dict()

    device_properties = cls.device_properties.get_dict()

    disk_size_mib = cls.disk_size_mib

    # find device type
    device_type = device_properties["device_type"]
    adapter_type = device_properties["disk_address"]["adapter_type"]

    schema_file = ""
    user_attrs = {}

    # find operation_type
    if data_source_ref:
        # TODO fetch from sever using uuid
        user_attrs["name"] = data_source_ref.get("name")
        if data_source_ref["kind"] == "app_package":
            operation_type = "cloneFromVMDiskPackage"

        elif data_source_ref["kind"] == "image":
            # TODO vmdisk name matching from nap-display map here
            operation_type = "cloneFromImageService"

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
        return ""
        if adapter_type == "SATA":
            if operation_type == "cloneFromImageService":
                schema_file = "ahv_vm_disk_sata_clone_from_image.py.jinja2"

            elif operation_type == "cloneFromVMDiskPackage":
                schema_file = "ahv_vm_disk_sata_clone_from_pkg.py.jinja2"

            elif operation_type == "emptyCdRom":
                schema_file = "ahv_vm_disk_pci_empty_cdrom.py.jinja2"

            else:
                LOG.error("Unknown operation type {}".format(operation_type))
                sys.exit(-1)

        elif adapter_type == "IDE":
            if operation_type == "cloneFromImageService":
                schema_file = "ahv_vm_disk_ide_clone_from_image.py.jinja2"

            elif operation_type == "cloneFromVMDiskPackage":
                schema_file = "ahv_vm_disk_ide_clone_from_pkg.py.jinja2"

            elif operation_type == "emptyCdRom":
                schema_file = "ahv_vm_disk_ide_empty_cdrom.py.jinja2"

            else:
                LOG.error("Unknown operation type {}".format(operation_type))
                sys.exit(-1)

        else:
            LOG.error("Unknown adapter type {}".format(adapter_type))
            sys.exit(-1)

    text = render_template(schema_file=schema_file, obj=user_attrs)
    return text.strip()
