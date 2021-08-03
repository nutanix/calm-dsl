from calm.dsl.builtins import read_local_file, basic_cred, ahv_vm
from calm.dsl.builtins import Provider, Ref
from calm.dsl.builtins import Substrate, Environment, readiness_probe
from calm.dsl.builtins import AhvVmDisk, AhvVmNic, AhvVmGC, AhvVmResources


NTNX_ACCOUNT_NAME = "NTNX_LOCAL_AZ"
NTNX_SUBNET = "vlan.0"
NTNX_SUBNET_CLUSTER = "calmdev1"
CENTOS_CI = "CentOS-7-cloudinit"
AWS_ACCOUNT_NAME = "aws_account"
AZURE_ACCOUNT_NAME = "azure_account"
GCP_ACCOUNT_NAME = "gcp_account"
VMWARE_ACCOUNT_NAME = "vmware_account"

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
    nics = [AhvVmNic(NTNX_SUBNET)]

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
            account=Ref.Account(NTNX_ACCOUNT_NAME),
            subnets=[
                Ref.Subnet(
                    name=NTNX_SUBNET,
                    cluster=NTNX_SUBNET_CLUSTER,
                )
            ],
        ),
        Provider.Aws(account=Ref.Account(AWS_ACCOUNT_NAME)),
        Provider.Gcp(account=Ref.Account(GCP_ACCOUNT_NAME)),
        Provider.Vmware(account=Ref.Account(VMWARE_ACCOUNT_NAME)),
    ]
