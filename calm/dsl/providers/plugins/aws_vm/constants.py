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
    POWER_STATE = {
        "RUNNING": "RUNNING",
        "REBOOTING": "REBOOTING",
        "STOPPED": "STOPPED",
        "ON": 'ON',
        "OFF": 'OFF'
    }
