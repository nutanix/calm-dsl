class AHV:
    DEVICE_TYPES = {"CD_ROM": "CDROM", "DISK": "DISK"}

    DEVICE_BUS = {
        "CDROM": {"SATA": "SATA", "IDE": "IDE"},
        "DISK": {"SCSI": "SCSI", "PCI": "PCI"},
    }
    IMAGE_TYPES = {"DISK": "DISK_IMAGE", "CDROM": "ISO_IMAGE"}

    GUEST_CUSTOMIZATION_SCRIPT_TYPES = ["cloud_init", "sysprep"]

    SYS_PREP_INSTALL_TYPES = ["FRESH", "PREPARED"]
    BOOT_TYPES = {"Legacy BIOS": "LEGACY", "UEFI": "UEFI"}
    OPERATION_TYPES = {
        "DISK": ["CLONE_FROM_IMAGE", "ALLOCATE_STORAGE_CONTAINER"],
        "CDROM": ["CLONE_FROM_IMAGE", "EMPTY_CDROM"],
    }
    OPERATING_SYSTEM = {"LINUX": "Linux", "WINODWS": "Windows"}
