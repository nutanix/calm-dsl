class AHV:
    VERSION = "nutanix/v1"
    SUBNETS = "{}/subnets". format(VERSION)
    IMAGES = "{}/images". format(VERSION)
    GROUPS = "{}/groups". format(VERSION)
    DEVICE_TYPES = {"CD_ROM": "CDROM", "DISK": "DISK"}

    DEVICE_BUS = {"SATA": "SATA", "IDE": "IDE"}
    DEVICE_BUS = {
        "CDROM": {"SATA": "SATA", "IDE": "IDE"},
        "DISK": {"SCSI": "SCSI", "PCI": "PCI"},
    }
    IMAGE_TYPES = {"DISK": "DISK_IMAGE", "CDROM": "ISO_IMAGE"}

    GUEST_CUSTOMIZATION_SCRIPT_TYPES = ["cloud_init", "sysprep"]

    SYS_PREP_INSTALL_TYPES = ["FRESH", "PREPARED"]
    BOOT_TYPES = {"Legacy BIOS": "LEGACY", "UEFI": "UEFI"}
