# Note: In given example, we not added environment reference anywhere.
# Project create command will pick one Environment module from file and attaches to project

import uuid
import json

from calm.dsl.builtins import Project, read_local_file, readiness_probe
from calm.dsl.builtins import Provider, Ref, ref
from calm.dsl.builtins import Substrate, Environment
from calm.dsl.builtins import AhvVmDisk, AhvVmNic, AhvVmGC
from calm.dsl.builtins import basic_cred, AhvVmResources, AhvVm


DSL_CONFIG = json.loads(read_local_file(".tests/config.json"))
CENTOS_CI = DSL_CONFIG["AHV"]["IMAGES"]["DISK"]["CENTOS_7_CLOUD_INIT"]
SQL_SERVER_IMAGE = DSL_CONFIG["AHV"]["IMAGES"]["CD_ROM"]["SQL_SERVER_2014_x64"]

# Accounts
ACCOUNTS = DSL_CONFIG["ACCOUNTS"]

NTNX_ACCOUNT_1 = ACCOUNTS["NUTANIX_PC"][0]
NTNX_ACCOUNT_1_NAME = NTNX_ACCOUNT_1["NAME"]
NTNX_ACCOUNT_1_SUBNET_1 = NTNX_ACCOUNT_1["SUBNETS"][0]["NAME"]
NTNX_ACCOUNT_1_SUBNET_1_CLUSTER = NTNX_ACCOUNT_1["SUBNETS"][0]["CLUSTER"]
NTNX_ACCOUNT_1_SUBNET_2 = NTNX_ACCOUNT_1["SUBNETS"][1]["NAME"]
NTNX_ACCOUNT_1_SUBNET_2_CLUSTER = NTNX_ACCOUNT_1["SUBNETS"][1]["CLUSTER"]

NTNX_ACCOUNT_2 = ACCOUNTS["NUTANIX_PC"][1]
NTNX_ACCOUNT_2_NAME = NTNX_ACCOUNT_2["NAME"]
NTNX_ACCOUNT_2_SUBNET_1 = NTNX_ACCOUNT_2["SUBNETS"][0]["NAME"]
NTNX_ACCOUNT_2_SUBNET_1_CLUSTER = NTNX_ACCOUNT_2["SUBNETS"][0]["CLUSTER"]

AWS_ACCOUNT = ACCOUNTS["AWS"][0]
AWS_ACCOUNT_NAME = AWS_ACCOUNT["NAME"]

AZURE_ACCOUNT = ACCOUNTS["AZURE"][0]
AZURE_ACCOUNT_NAME = AZURE_ACCOUNT["NAME"]

GCP_ACCOUNT = ACCOUNTS["GCP"][0]
GCP_ACCOUNT_NAME = GCP_ACCOUNT["NAME"]

VMWARE_ACCOUNT = ACCOUNTS["VMWARE"][0]
VMWARE_ACCOUNT_NAME = VMWARE_ACCOUNT["NAME"]

K8S_ACCOUNT = ACCOUNTS["K8S"][0]
K8S_ACCOUNT_NAME = K8S_ACCOUNT["NAME"]

USER = DSL_CONFIG["USERS"][0]
USER_NAME = USER["NAME"]

CENTOS_KEY = read_local_file("keys/centos")
CENTOS_PUBLIC_KEY = read_local_file("keys/centos_pub")

Centos = basic_cred("centos", CENTOS_KEY, name="Centos", type="KEY", default=True)


class MyAhvLinuxVmResources(AhvVmResources):

    memory = 4
    vCPUs = 2
    cores_per_vCPU = 1
    disks = [
        AhvVmDisk.Disk.Scsi.cloneFromImageService(CENTOS_CI, bootable=True),
    ]
    nics = [AhvVmNic(NTNX_ACCOUNT_1_SUBNET_1)]

    guest_customization = AhvVmGC.CloudInit(
        config={
            "users": [
                {
                    "name": "centos",
                    "ssh-authorized-keys": [CENTOS_PUBLIC_KEY],
                    "sudo": ["ALL=(ALL) NOPASSWD:ALL"],
                }
            ]
        }
    )

    serial_ports = {0: False, 1: False, 2: True, 3: True}


class MyAhvLinuxVm(AhvVm):

    resources = MyAhvLinuxVmResources
    categories = {"AppFamily": "Backup", "AppType": "Default"}


class AhvVmSubstrate(Substrate):
    """AHV VM config given by reading a spec file"""

    provider_spec = MyAhvLinuxVm
    readiness_probe = readiness_probe(disabled=True)


class MyAhvWindowsVmResources(AhvVmResources):

    memory = 4
    vCPUs = 2
    cores_per_vCPU = 1
    disks = [
        AhvVmDisk.CdRom.Sata.cloneFromImageService(SQL_SERVER_IMAGE, bootable=True),
    ]
    nics = [AhvVmNic(NTNX_ACCOUNT_2_SUBNET_1)]

    guest_customization = AhvVmGC.Sysprep.FreshScript(
        filename="scripts/sysprep_script.xml"
    )

    serial_ports = {0: False, 1: False, 2: True, 3: True}


class MyAhvWindowsVm(AhvVm):

    resources = MyAhvWindowsVmResources
    categories = {"AppFamily": "Backup", "AppType": "Default"}


class AhvWindowsVmSubstrate(Substrate):
    """AHV VM config given by reading a spec file"""

    provider_spec = MyAhvWindowsVm
    os_type = "Windows"
    readiness_probe = readiness_probe(disabled=True)


class ProjEnvironment1(Environment):

    substrates = [AhvVmSubstrate]
    credentials = [Centos]
    providers = [
        Provider.Ntnx(
            account=Ref.Account(NTNX_ACCOUNT_1_NAME),
            subnets=[
                Ref.Subnet(
                    name=NTNX_ACCOUNT_1_SUBNET_1,
                    cluster=NTNX_ACCOUNT_1_SUBNET_1_CLUSTER,
                )
            ],
        ),
        Provider.Aws(account=Ref.Account(AWS_ACCOUNT_NAME)),
        Provider.Azure(account=Ref.Account(AZURE_ACCOUNT_NAME)),
    ]


class ProjEnvironment2(Environment):

    substrates = [AhvWindowsVmSubstrate]
    credentials = [Centos]
    providers = [
        Provider.Ntnx(
            account=Ref.Account(NTNX_ACCOUNT_2_NAME),
            subnets=[
                Ref.Subnet(
                    name=NTNX_ACCOUNT_2_SUBNET_1,
                    cluster=NTNX_ACCOUNT_2_SUBNET_1_CLUSTER,
                )
            ],
        ),
        Provider.Gcp(account=Ref.Account(GCP_ACCOUNT_NAME)),
    ]


class SampleDslProject(Project):
    """Sample DSL Project with environments"""

    providers = [
        Provider.Ntnx(
            account=Ref.Account(NTNX_ACCOUNT_1_NAME),
            subnets=[
                Ref.Subnet(
                    name=NTNX_ACCOUNT_1_SUBNET_2,
                    cluster=NTNX_ACCOUNT_1_SUBNET_2_CLUSTER,
                )
            ],
        ),
        Provider.Gcp(account=Ref.Account(GCP_ACCOUNT_NAME)),
        Provider.Vmware(account=Ref.Account(VMWARE_ACCOUNT_NAME)),
        Provider.K8s(account=Ref.Account(K8S_ACCOUNT_NAME)),
    ]

    users = [Ref.User(USER_NAME)]

    envs = [ProjEnvironment1, ProjEnvironment2]
    default_environment = ref(ProjEnvironment1)
    quotas = {
        "vcpus": 1,
        "storage": 2,
        "memory": 1,
    }
