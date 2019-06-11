class AHV:
    SUBNETS = "subnets"
    IMAGES = "images"
    GROUPS = "groups"
    DEVICE_TYPES = {"CD_ROM": "CDROM", "DISK": "DISK"}

    DEVICE_BUS = {"SATA": "SATA", "IDE": "IDE"}

    GUEST_CUSTOMIZATION_SCRIPT_TYPES = ["cloud_init", "sysprep"]


class AWS:
    MACHINE_TYPES = "aws/machine_types"
    VOLUME_TYPES = "aws/volume_types"
    AVAILABILTY_ZONES = "aws/availability_zones"
    MIXED_IMAGES = "aws/mixed_images"
    ROLES = "aws/roles"
    KEY_PAIRS = "aws/key_pairs"
    VPCS = "aws/vpcs"
    SECURITY_GROUPS = "aws/security_groups"
    SUBNETS = "aws/subnets"
