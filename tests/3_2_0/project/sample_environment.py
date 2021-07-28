import json

from calm.dsl.builtins import read_local_file, basic_cred, ahv_vm
from calm.dsl.builtins import Provider, Ref
from calm.dsl.builtins import Substrate, Environment, readiness_probe
from calm.dsl.builtins import AhvVmDisk, AhvVmNic, AhvVmGC, AhvVmResources

DSL_CONFIG = json.loads(read_local_file(".tests/config.json"))
CENTOS_CI = DSL_CONFIG["AHV"]["IMAGES"]["DISK"]["CENTOS_7_CLOUD_INIT"]

# Accounts
ACCOUNTS = DSL_CONFIG["ACCOUNTS"]

NTNX_ACCOUNT_1 = ACCOUNTS["NUTANIX_PC"][0]
NTNX_ACCOUNT_1_NAME = NTNX_ACCOUNT_1["NAME"]
NTNX_ACCOUNT_1_SUBNET_1 = NTNX_ACCOUNT_1["SUBNETS"][0]["NAME"]
NTNX_ACCOUNT_1_SUBNET_1_CLUSTER = NTNX_ACCOUNT_1["SUBNETS"][0]["CLUSTER"]

AWS_ACCOUNT = ACCOUNTS["AWS"][0]
AWS_ACCOUNT_NAME = AWS_ACCOUNT["NAME"]

AZURE_ACCOUNT = ACCOUNTS["AZURE"][0]
AZURE_ACCOUNT_NAME = AZURE_ACCOUNT["NAME"]

GCP_ACCOUNT = ACCOUNTS["GCP"][0]
GCP_ACCOUNT_NAME = GCP_ACCOUNT["NAME"]

VMWARE_ACCOUNT = ACCOUNTS["VMWARE"][0]
VMWARE_ACCOUNT_NAME = VMWARE_ACCOUNT["NAME"]

CENTOS_KEY = read_local_file(".tests/keys/centos")
CENTOS_PUBLIC_KEY = read_local_file(".tests/keys/centos_pub")

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


class AhvVmSubstrate(Substrate):
    """AHV VM config given by reading a spec file"""

    provider_spec = ahv_vm(
        resources=MyAhvLinuxVmResources,
        categories={"AppFamily": "Backup", "AppType": "Default"},
    )
    readiness_probe = readiness_probe(disabled=True)


class SampleDslEnvironment(Environment):

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
        Provider.Gcp(account=Ref.Account(GCP_ACCOUNT_NAME)),
        Provider.Vmware(account=Ref.Account(VMWARE_ACCOUNT_NAME)),
    ]
