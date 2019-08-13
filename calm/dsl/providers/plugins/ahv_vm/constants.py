class AHV:
    SUBNETS = "subnets"
    IMAGES = "images"
    GROUPS = "groups"
    DEVICE_TYPES = {"CD_ROM": "CDROM", "DISK": "DISK"}

    DEVICE_BUS = {"SATA": "SATA", "IDE": "IDE"}
    DEVICE_BUS = {
        "CDROM": {"SATA": "SATA", "IDE": "IDE"},
        "DISK": {"SCSI": "SCSI", "PCI": "PCI"},
    }

    GUEST_CUSTOMIZATION_SCRIPT_TYPES = ["cloud_init", "sysprep"]

    SYS_PREP_INSTALL_TYPES = ["Fresh", "Prepared"]
