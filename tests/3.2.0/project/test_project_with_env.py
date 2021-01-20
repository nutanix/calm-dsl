# Note: In given example, we not added environment reference anywhere.
# Project create command will pick one Environment module from file and attaches to project

import uuid

from calm.dsl.builtins import Project, read_local_file, readiness_probe
from calm.dsl.builtins import Provider, Ref, ref
from calm.dsl.builtins import Substrate, Environment
from calm.dsl.builtins import AhvVmDisk, AhvVmNic, AhvVmGC
from calm.dsl.builtins import basic_cred, AhvVmResources, AhvVm


CENTOS_KEY = read_local_file("keys/centos")
CENTOS_PUBLIC_KEY = read_local_file("keys/centos_pub")

Centos = basic_cred("centos", CENTOS_KEY, name="Centos", type="KEY", default=True)


class MyAhvLinuxVmResources(AhvVmResources):

    memory = 4
    vCPUs = 2
    cores_per_vCPU = 1
    disks = [
        AhvVmDisk.Disk.Scsi.cloneFromImageService("Centos7HadoopMaster", bootable=True),
    ]
    nics = [AhvVmNic("vlan1211")]

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
        AhvVmDisk.Disk.Scsi.cloneFromImageService("WindowsServer2016", bootable=True),
    ]
    nics = [AhvVmNic("vlan1211")]

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


class ProjEnvironment(Environment):

    substrates = [AhvVmSubstrate]
    credentials = [Centos]
    providers = [
        Provider.Ntnx(
            account=Ref.Account("NTNX_LOCAL_AZ"),
            subnets=[Ref.Subnet(name="vlan1211")],
        ),
        Provider.Aws(account=Ref.Account("aws_cloudb9540")),
        Provider.Azure(account=Ref.Account("azure_cloudfdbb0")),
        Provider.Gcp(account=Ref.Account("gcp_cloudd9361")),
        Provider.Vmware(account=Ref.Account("vmware_cloudb624a")),
    ]


class TestDslProjectWithEnv14(Project):
    """Sample DSL Project with environments"""

    providers = [
        Provider.Ntnx(
            account=Ref.Account("NTNX_LOCAL_AZ"),
            subnets=[Ref.Subnet(name="vlan1211")],
        ),
        Provider.Ntnx(
            account=Ref.Account("multipc_account4a0db9311a"),
            subnets=[Ref.Subnet(name="vlan1211")],
        ),
        Provider.Aws(account=Ref.Account("aws_cloudb9540")),
        Provider.Azure(account=Ref.Account("azure_cloudfdbb0")),
        Provider.Gcp(account=Ref.Account("gcp_cloudd9361")),
        Provider.Vmware(account=Ref.Account("vmware_cloudb624a")),
    ]

    users = []

    envs = [ProjEnvironment]
    default_environment = ref(ProjEnvironment)
    quotas = {
        "vcpus": 1,
        "storage": 2,
        "memory": 1,
    }


# NOTE this is used for tests. Environment name is changed to prevent same name for multiple environments
ProjEnvironment.__name__ = "{}_{}".format(
    ProjEnvironment.__name__, str(uuid.uuid4())[:10]
)
