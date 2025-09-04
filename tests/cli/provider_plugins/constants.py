class AWS:
    """AWS Constants for cli provider_plugins tests"""

    PROJECTS = ["default"]
    REGIONS = ["us-east-1"]
    AVAILABILITY_ZONES = ["us-east-1a"]
    MACHINE_IMAGES = ["DND_CENTOS_QA"]
    IAM_ROLES = ["aws-elasticbeanstalk-ec2-role"]
    KEY_PAIRS = ["calm-blueprints"]
    VPC_IDS = ["vpc-ffd54d98"]
    SECURITY_GROUPS = ["sg-184ead62"]
    SUBNETS = ["subnet-c599a5ef"]
    VOLUME_TYPES = ["Provisioned IOPS SSD"]
    INSTANCE_TYPES = ["t2.nano"]


class AZURE:
    """Azure Constants for cli provider_plugin tests"""

    PROJECTS = ["default"]
    RESOURCE_GROUPS = ["calmrg"]
    LOCATIONS = ["East US 2"]
    HW_PROFILES = ["Standard_DS1_v2", "Standard_D2_v2"]
    PUBLISHERS = ["Canonical"]
    IMAGE_OFFERS = ["0001-com-ubuntu-server-jammy"]
    IMAGE_SKUS = ["22_04-lts-gen2"]
    IMAGE_VERSIONS = ["22.04.202506200"]
    SECURITY_GROUPS = ["DND-CENTOS-IMAGE-nsg"]
    VIRTUAL_NETWORKS = ["calm-virtual-network-eastus2"]
    SUBNETS = ["subnet1", "default"]
    CUSTOM_IMAGES = ["DND-CENTOS-IMAGE"]
    AVAILABILITY_SETS = ["test_as_esha"]
