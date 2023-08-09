class AWS:
    MACHINE_TYPES = "aws/machine_types"
    VOLUME_TYPES = "aws/volume_types"
    AVAILABILTY_ZONES = "aws/availability_zones"
    MIXED_IMAGES = "aws/mixed_images"
    IMAGES = "images"
    ROLES = "aws/roles"
    KEY_PAIRS = "aws/key_pairs"
    VPCS = "aws/vpcs"
    SECURITY_GROUPS = "aws/security_groups"
    SUBNETS = "aws/subnets"
    POWER_STATE = {
        "RUNNING": "RUNNING",
        "REBOOTING": "REBOOTING",
        "STOPPED": "STOPPED",
        "ON": "ON",
        "OFF": "OFF",
    }

    VOLUME_TYPE_MAP = {
        "Provisioned IOPS SSD": "IO1",
        "EBS Magnetic HDD": "STANDARD",
        "Cold HDD": "SC1",
        "Throughput Optimized HDD": "ST1",
        "General Purpose SSD": "GP2",
    }

    DeviceMountPoints = {  # Constants from calm-ui repoitory
        "/dev/sdb": "/dev/sdb",
        "/dev/sdc": "/dev/sdc",
        "/dev/sdd": "/dev/sdd",
        "/dev/sde": "/dev/sde",
        "/dev/sdf": "/dev/sdf",
        "/dev/sdg": "/dev/sdg",
        "/dev/sdh": "/dev/sdh",
        "/dev/sdi": "/dev/sdi",
        "/dev/sdj": "/dev/sdj",
        "/dev/sdk": "/dev/sdk",
        "/dev/sdl": "/dev/sdl",
    }
