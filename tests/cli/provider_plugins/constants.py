class AWS:
    """AWS Constants for cli provider_plugins tests"""

    PROJECTS = ["default"]
    REGIONS = ["us-east-1"]
    AVAILABILITY_ZONES = ["us-east-1a"]
    MACHINE_IMAGES = [
        "CentOS Linux 7 x86_64 HVM EBS 1704_01-b7ee8a69-ee97-4a49-9e68-afaee216db2e-ami-d52f5bc3.4"
    ]
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
    HW_PROFILES = ["Standard_D1_v2", "Standard_D2_v2"]
    PUBLISHERS = ["Canonical"]
    IMAGE_OFFERS = ["UbuntuServer"]
    IMAGE_SKUS = ["18.04-LTS"]
    IMAGE_VERSIONS = ["18.04.201903121"]
    SECURITY_GROUPS = ["DND-CENTOS-IMAGE-nsg"]
    VIRTUAL_NETWORKS = ["calm-virtual-network-eastus2"]
    SUBNETS = ["subnet1", "default"]
    CUSTOM_IMAGES = ["DND-CENTOS-IMAGE"]
    AVAILABILITY_SETS = ["test_as_esha"]
