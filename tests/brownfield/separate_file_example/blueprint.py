import json

from calm.dsl.builtins import AhvVmDisk, AhvVmNic, AhvVmGC
from calm.dsl.builtins import ref, basic_cred, AhvVmResources, AhvVm
from calm.dsl.builtins import read_local_file, readiness_probe

from calm.dsl.builtins import Service, Package, Substrate
from calm.dsl.builtins import Deployment, Profile, Blueprint
from calm.dsl.builtins import CalmVariable, CalmTask, action
from calm.dsl.builtins import Metadata, Ref


CENTOS_KEY = read_local_file(".tests/keys/centos")
CENTOS_PUBLIC_KEY = read_local_file(".tests/keys/centos_pub")

# projects
DSL_CONFIG = json.loads(read_local_file(".tests/config.json"))
CENTOS_CI = DSL_CONFIG["AHV"]["IMAGES"]["DISK"]["CENTOS_7_CLOUD_INIT"]
PROJECT = DSL_CONFIG["PROJECTS"]["PROJECT1"]
PROJECT_NAME = PROJECT["NAME"]
NETWORK1 = DSL_CONFIG["AHV"]["NETWORK"]["VLAN1211"]

Centos = basic_cred("centos", CENTOS_KEY, name="Centos", type="KEY", default=True)


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


class MyAhvVmResources(AhvVmResources):

    memory = 2
    vCPUs = 1
    cores_per_vCPU = 1
    disks = [AhvVmDisk.Disk.Scsi(CENTOS_CI, bootable=True)]
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
    readiness_probe = readiness_probe(
        connection_type="SSH",
        disabled=False,
        editables_list=["connection_port", "retries"],
        delay_secs="60",
        retries="5",
    )


class AhvVmDeployment(Deployment):
    """Sample deployment pulling in service and substrate references"""

    packages = [ref(AhvVmPackage)]
    substrate = ref(AhvVmSubstrate)


class AhvVmProfile(Profile):
    """Sample application profile with variables"""

    nameserver = CalmVariable.Simple("10.40.64.15", label="Local DNS resolver")
    foo1 = CalmVariable.Simple("bar1", runtime=True)
    foo2 = CalmVariable.Simple("bar2", runtime=True)

    deployments = [AhvVmDeployment]

    @action
    def test_profile_action():
        """Sample description for a profile action"""
        CalmTask.Exec.ssh(name="Task5", script='echo "Hello"', target=ref(AhvVmService))


class AhvBlueprint(Blueprint):
    """Sample Bp that used ahv_vm_helpers"""

    credentials = [Centos]
    services = [AhvVmService]
    packages = [AhvVmPackage]
    substrates = [AhvVmSubstrate]
    profiles = [AhvVmProfile]


class BpMetadata(Metadata):

    project = Ref.Project(PROJECT_NAME)
