import json

from calm.dsl.builtins import AhvVmDisk, AhvVmNic, AhvVmGC
from calm.dsl.builtins import ref, AhvVmResources, AhvVm, Ref, Metadata
from calm.dsl.builtins import vm_disk_package, read_local_file, basic_cred

from calm.dsl.builtins import Service, Package, Substrate
from calm.dsl.builtins import Deployment, Profile, Blueprint
from calm.dsl.builtins import CalmVariable, CalmTask, action

CENTOS_KEY = read_local_file(".tests/keys/centos")
CENTOS_PUBLIC_KEY = read_local_file(".tests/keys/centos_pub")

DSL_CONFIG = json.loads(read_local_file(".tests/config.json"))
CENTOS_CI = DSL_CONFIG["AHV"]["IMAGES"]["DISK"]["CENTOS_7_CLOUD_INIT"]
NETWORK1 = DSL_CONFIG["AHV"]["NETWORK"]["VLAN1211"]  # TODO change network constants

# project constants
PROJECT = DSL_CONFIG["PROJECTS"]["PROJECT1"]
PROJECT_NAME = PROJECT["NAME"]
ENV_NAME = PROJECT["ENVIRONMENTS"][0]["NAME"]
ACCOUNT_NAME = PROJECT["ACCOUNTS"]["NUTANIX_PC"][0]["NAME"]


Centos = basic_cred("centos", CENTOS_KEY, name="Centos", type="KEY", default=True)

Era_Disk = vm_disk_package(
    name="era_disk",
    config={
        # By default image type is set to DISK_IMAGE
        "image": {
            "source": "http://download.nutanix.com/era/1.1.1/ERA-Server-build-1.1.1-340d9db1118eac81219bec98507d4982045d8799.qcow2"
        }
    },
)
Virtio_CdRom = vm_disk_package(
    name="virtio_cdrom",
    config={
        "image": {
            "type": "ISO_IMAGE",
            "source": "http://10.40.64.33/GoldImages/NuCalm/ISO/Nutanix-VirtIO-1.1.4.iso",
        }
    },
)


class AhvVmService(Service):
    """Sample mysql service"""

    ENV = CalmVariable.Simple("DEV")


class AhvVmPackage(Package):
    """Example package with variables, install tasks and link to service"""

    foo = CalmVariable.Simple("bar")
    services = [ref(AhvVmService)]

    @action
    def __install__():
        CalmTask.Exec.ssh(name="Task1", script="echo @@{foo}@@")


class AhvVmPackage2(AhvVmPackage):
    pass


class MyAhvVmResources(AhvVmResources):

    memory = 4
    vCPUs = 2
    cores_per_vCPU = 1
    disks = [
        AhvVmDisk(CENTOS_CI),
    ]
    nics = [AhvVmNic(NETWORK1)]

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


class MyAhvVm(AhvVm):

    resources = MyAhvVmResources
    categories = {"AppFamily": "Backup", "AppType": "Default"}


class AhvVmSubstrate(Substrate):
    """AHV VM config given by reading a spec file"""

    provider_spec = MyAhvVm
    account = Ref.Account(ACCOUNT_NAME)


class MyAhvVmResources2(AhvVmResources):

    memory = 4
    vCPUs = 2
    cores_per_vCPU = 1
    disks = [
        AhvVmDisk(CENTOS_CI),
        AhvVmDisk.CdRom.Ide.emptyCdRom(),
    ]
    nics = [AhvVmNic(NETWORK1)]

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


class MyAhvVm2(AhvVm):

    resources = MyAhvVmResources2


class AhvVmSubstrate2(Substrate):
    """AHV VM config given by reading a spec file"""

    provider_spec = MyAhvVm2
    account = Ref.Account(ACCOUNT_NAME)


class AhvVmDeployment(Deployment):
    """Sample deployment pulling in service and substrate references"""

    packages = [ref(AhvVmPackage)]
    substrate = ref(AhvVmSubstrate)


class AhvVmDeployment2(Deployment):
    """Sample deployment pulling in service and substrate references"""

    packages = [ref(AhvVmPackage2)]
    substrate = ref(AhvVmSubstrate2)


class AhvVmProfile(Profile):
    """Sample application profile with variables"""

    nameserver = CalmVariable.Simple("10.40.64.15", label="Local DNS resolver")
    foo1 = CalmVariable.Simple("bar1", runtime=True)
    foo2 = CalmVariable.Simple("bar2", runtime=True)

    deployments = [AhvVmDeployment]
    environments = [Ref.Environment(name=ENV_NAME)]

    @action
    def test_profile_action():
        """Sample description for a profile action"""
        CalmTask.Exec.ssh(name="Task5", script='echo "Hello"', target=ref(AhvVmService))


class AhvVmProfile2(Profile):
    """Sample application profile with variables"""

    nameserver = CalmVariable.Simple("10.40.64.15", label="Local DNS resolver")
    foo1 = CalmVariable.Simple("bar1", runtime=True)
    foo2 = CalmVariable.Simple("bar2", runtime=True)

    deployments = [AhvVmDeployment2]
    environments = [Ref.Environment(name=ENV_NAME)]

    @action
    def test_profile_action():
        """Sample description for a profile action"""
        CalmTask.Exec.ssh(name="Task5", script='echo "Hello"', target=ref(AhvVmService))


class AhvBlueprint(Blueprint):
    """Sample Bp that used ahv_vm_helpers"""

    credentials = [Centos]
    services = [AhvVmService]
    packages = [AhvVmPackage, AhvVmPackage2, Era_Disk, Virtio_CdRom]
    substrates = [AhvVmSubstrate, AhvVmSubstrate2]
    profiles = [AhvVmProfile, AhvVmProfile2]


class BpMetadata(Metadata):

    project = Ref.Project(PROJECT_NAME)
