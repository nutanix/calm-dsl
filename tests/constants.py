# -*- coding: utf-8 -*-
"""constants"""
#
# pylint: disable=missing-docstring, invalid-name, line-too-long
class BP_SPEC:
    PROJECT_NAME_DEFAULT = "default"


class PROVIDER:
    class AHV:
        NIC = "vlan1211"
        LINIX_IMAGE = "Centos7HadoopMaster"

    class VMWARE:
        DND_CENTOS_WITH_NIC_J_TEMPLATE = "503e35e6-e621-64bf-86db-a51115f7ab28"
        DATASTORE = "ds:///vmfs/volumes/f6a8bff3-a29c7b8e/"
        HOST = "00000000-0000-0000-0000-ac1f6bba7912"
        TAG_ID = (
            "urn:vmomi:InventoryServiceTag:67988884-a4c3-414f-ba10-b27e37b2ffb5:GLOBAL"
        )

        class VNIC:
            NET_NAME_API = "key-vim.host.PortGroup-vlan.112"
            NIC_TYPE_API = "e1000"

        class SCSI_CONTROLLER:
            CONTROLLER_TYPE_API = "VirtualLsiLogicSASController"

    class AWS:
        SECGROUPID = "sg-184ead62"
        AMIID = "ami-0ccec2041ac92b449"
        DEFAULT_KEYNAME = "calm-blueprints"
        DEFAULT_REGION = "us-east-1"
        DEFAULT_PROFILE = "aws-elasticbeanstalk-ec2-role"
        DEFAULT_SUBNET = "subnet-c599a5ef"
        DEFAULT_VPC = "vpc-ffd54d98"

    class GCP:
        SOURCE_IMAGE = "https://www.googleapis.com/compute/v1/projects/nucalm-devopos/global/images/centos-7"
        NETWORK_NAME = "https://www.googleapis.com/compute/v1/projects/nucalm-devopos/global/networks/default"
        SUBNETWORK_NAME = "https://www.googleapis.com/compute/v1/projects/nucalm-devopos/regions/us-central1/subnetworks/default"
        CLIENT_EMAIL = "108048128720-compute@developer.gserviceaccount.com"
        ITEMS = "https-server"
        MACHINE_TYPE = "https://www.googleapis.com/compute/v1/projects/nucalm-devopos/zones/us-central1-c/machineTypes/f1-micro"
        DEFAULT_ZONE = "us-central1-c"

    class AZURE:
        PUBLIC_IMAGE_PUBLISHER = "Canonical"
        PUBLIC_IMAGE_OFFER = "0001-com-ubuntu-server-jammy"
        PUBLIC_IMAGE_SKU = "22_04-lts-gen2"
        PUBLIC_IMAGE_VERSION = "22.04.202506200"
        IMAGE_MARKETPLACE = "Marketplace"
        SECURITY_GROUP = "calm-nsg1"
        VIRTUAL_NETWORK = "calm-virtual-network-eastus2"
        SUBNET_NAME = "default"
        RESOURCE_GROUP = "calmrg2"
        RG_OPERATION = "use_existing"
        NSG_ID = "/subscriptions/c88c75b1-c860-411e-b920-a48d02a8ce45/resourceGroups/calmrg2/providers/Microsoft.Network/networkSecurityGroups/calm-nsg1"
        VNET_ID = "/subscriptions/c88c75b1-c860-411e-b920-a48d02a8ce45/resourceGroups/calmrg/providers/Microsoft.Network/virtualNetworks/calm-virtual-network-eastus2"
        SUBNET_ID = "/subscriptions/c88c75b1-c860-411e-b920-a48d02a8ce45/resourceGroups/calmrg/providers/Microsoft.Network/virtualNetworks/calm-virtual-network-eastus2/subnets/default"
