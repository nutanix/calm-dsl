import json

from calm.dsl.builtins import AhvVmDisk, AhvVmNic, AhvVmGC
from calm.dsl.builtins import ref, basic_cred
from calm.dsl.builtins import vm_disk_package, read_local_file

from calm.dsl.builtins import Service, Package, Substrate
from calm.dsl.builtins import Deployment, Profile, Blueprint
from calm.dsl.builtins import CalmVariable, CalmTask, action
from calm.dsl.builtins import Ref, Metadata
from calm.dsl.builtins import AhvVmRecoveryResources, ahv_vm_recovery_spec


CENTOS_KEY = read_local_file(".tests/keys/centos")
CENTOS_PUBLIC_KEY = read_local_file(".tests/keys/centos_pub")

DSL_CONFIG = json.loads(read_local_file(".tests/config.json"))
NTNX_LOCAL_ACCOUNT = DSL_CONFIG["ACCOUNTS"]["NTNX_LOCAL_AZ"]
PROJECT = DSL_CONFIG["PROJECTS"]["PROJECT1"]
PROJECT_NAME = PROJECT["NAME"]
NETWORK1 = DSL_CONFIG["AHV"]["NETWORK"]["VLAN1211"]

VM_RECOVERY_POINT_NAME = read_local_file("vm_rp_name")

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


# [NumVcpusPerSocket, NumSockets, MemorySizeMb, NicList, GPUList, vm_name] can be overrided
class MyAhvVmResources(AhvVmRecoveryResources):

    memory = 4
    vCPUs = 2
    cores_per_vCPU = 1
    nics = [AhvVmNic(NETWORK1)]


# Only CrashConsistent vm_recovery_point are allowed
class AhvVmSubstrate(Substrate):
    """AHV VM config given by reading a spec file"""

    provider_type = "AHV_VM"
    vm_recovery_spec = ahv_vm_recovery_spec(
        recovery_point=Ref.RecoveryPoint(name=VM_RECOVERY_POINT_NAME),
        vm_name="AhvRestoredVm",
        vm_override_resources=MyAhvVmResources,
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


class AhvRPBlueprint(Blueprint):
    """Sample Bp that used ahv_vm_helpers"""

    credentials = [Centos]
    services = [AhvVmService]
    packages = [AhvVmPackage, Era_Disk]
    substrates = [AhvVmSubstrate]
    profiles = [AhvVmProfile]


class BpMetadata(Metadata):

    project = Ref.Project(PROJECT_NAME)
