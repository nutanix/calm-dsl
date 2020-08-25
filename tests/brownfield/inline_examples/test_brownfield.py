from calm.dsl.builtins import ref, basic_cred
from calm.dsl.builtins import vm_disk_package, read_local_file
from calm.dsl.builtins import Service, Package, Substrate
from calm.dsl.builtins import Profile, Blueprint
from calm.dsl.builtins import CalmVariable, CalmTask, action
from calm.dsl.builtins import Brownfield as BF


CENTOS_KEY = read_local_file("keys/centos")
CENTOS_PUBLIC_KEY = read_local_file("keys/centos_pub")

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


class AhvVmService2(AhvVmService):
    """Sample mysql service"""

    pass


class AhvVmService3(AhvVmService):
    """Sample mysql service"""

    pass


class AhvVmPackage(Package):
    """Example package with variables, install tasks and link to service"""

    foo = CalmVariable.Simple("bar")
    services = [ref(AhvVmService)]

    @action
    def __install__():
        CalmTask.Exec.ssh(name="Task1", script="echo @@{foo}@@")


class AhvVmPackage2(AhvVmPackage):
    """Example package with variables, install tasks and link to service"""

    services = [ref(AhvVmService2)]


class AhvVmPackage3(AhvVmPackage):
    """Example package with variables, install tasks and link to service"""

    services = [ref(AhvVmService3)]


class AhvVmSubstrate(Substrate):
    """AHV VM config given by reading a spec file"""

    provider_spec = {}


class AhvVmSubstrate2(AhvVmSubstrate):
    """AHV VM config given by reading a spec file"""

    pass


class AhvVmSubstrate3(AhvVmSubstrate):
    """AHV VM config given by reading a spec file"""

    pass


class BFAhvVmDeployment(BF.Deployment):
    """Sample deployment pulling in service and substrate references"""

    packages = [ref(AhvVmPackage)]
    substrate = ref(AhvVmSubstrate)

    instances = [BF.Vm.Ahv("Vm3")]


class BFAhvVmDeployment2(BF.Deployment):
    """Sample deployment pulling in service and substrate references"""

    packages = [ref(AhvVmPackage2)]
    substrate = ref(AhvVmSubstrate2)

    instances = [
        BF.Vm.Ahv("Test_Runtime_App_1597398086-2", ip_address=["10.46.34.122"])
    ]


class BFAhvVmDeployment3(BF.Deployment):
    """Sample deployment pulling in service and substrate references"""

    packages = [ref(AhvVmPackage3)]
    substrate = ref(AhvVmSubstrate3)

    instances = [
        BF.Vm.Ahv("Test_Runtime_App_1597398086-1", ip_address=["10.46.34.123"])
    ]


class AhvVmProfile(Profile):
    """Sample application profile with variables"""

    nameserver = CalmVariable.Simple("10.40.64.15", label="Local DNS resolver")
    foo1 = CalmVariable.Simple("bar1", runtime=True)
    foo2 = CalmVariable.Simple("bar2", runtime=True)

    deployments = [BFAhvVmDeployment, BFAhvVmDeployment2, BFAhvVmDeployment3]

    @action
    def test_profile_action():
        """Sample description for a profile action"""
        CalmTask.Exec.ssh(name="Task5", script='echo "Hello"', target=ref(AhvVmService))


class AhvBlueprint(Blueprint):
    """Sample Bp that used ahv_vm_helpers"""

    credentials = [Centos]
    services = [AhvVmService, AhvVmService2, AhvVmService3]
    packages = [AhvVmPackage, Era_Disk, AhvVmPackage2, AhvVmPackage3]
    substrates = [AhvVmSubstrate, AhvVmSubstrate2, AhvVmSubstrate3]
    profiles = [AhvVmProfile]
