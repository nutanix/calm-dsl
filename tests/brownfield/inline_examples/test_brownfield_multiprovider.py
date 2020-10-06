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


class AwsVmService(Service):
    """Sample mysql service"""

    pass


class AzureVmService(Service):
    """Sample mysql service"""

    pass


class GcpVmService(Service):
    """Sample mysql service"""

    pass


class AhvVmPackage(Package):
    """Example package with variables, install tasks and link to service"""

    foo = CalmVariable.Simple("bar")
    services = [ref(AhvVmService)]

    @action
    def __install__():
        CalmTask.Exec.ssh(name="Task1", script="echo @@{foo}@@")


class AwsVmPackage(Package):
    """Example package with variables, install tasks and link to service"""

    services = [ref(AwsVmService)]


class AzureVmPackage(Package):
    """Example package with variables, install tasks and link to service"""

    services = [ref(AzureVmService)]


class GcpVmPackage(Package):
    """Example package with variables, install tasks and link to service"""

    services = [ref(GcpVmService)]


class AhvVmSubstrate(Substrate):
    """AHV VM config given by reading a spec file"""

    provider_spec = {}


class AwsVmSubstrate(Substrate):
    """AWS VM config given by reading a spec file"""

    provider_type = "AWS_VM"
    provider_spec = {}


class AzureVmSubstrate(Substrate):
    """AZURE VM config given by reading a spec file"""

    provider_type = "AZURE_VM"
    provider_spec = {}


class GcpVmSubstrate(Substrate):
    """GCP VM config given by reading a spec file"""

    provider_type = "GCP_VM"
    provider_spec = {}


class BFAhvVmDeployment(BF.Deployment):
    """Sample deployment pulling in service and substrate references"""

    packages = [ref(AhvVmPackage)]
    substrate = ref(AhvVmSubstrate)

    instances = [BF.Vm.Ahv("Vm3")]


class BFAwsVmDeployment(BF.Deployment):
    """Sample deployment pulling in service and substrate references"""

    packages = [ref(AwsVmPackage)]
    substrate = ref(AwsVmSubstrate)

    instances = [BF.Vm.Aws("vm-0-200818-013427")]


class BFAzureVmDeployment(BF.Deployment):
    """Sample deployment pulling in service and substrate references"""

    packages = [ref(AzureVmPackage)]
    substrate = ref(AzureVmSubstrate)

    instances = [BF.Vm.Azure("tp-ins-a3bf9-0")]


class BFGcpVmDeployment2(BF.Deployment):
    """Sample deployment pulling in service and substrate references"""

    packages = [ref(GcpVmPackage)]
    substrate = ref(GcpVmSubstrate)

    instances = [BF.Vm.Gcp("delete-gcp-utest-c92edf4a-c212-478d-bf97-820fe68eee7f")]


class AhvVmProfile(Profile):
    """Sample application profile with variables"""

    nameserver = CalmVariable.Simple("10.40.64.15", label="Local DNS resolver")
    foo1 = CalmVariable.Simple("bar1", runtime=True)
    foo2 = CalmVariable.Simple("bar2", runtime=True)

    deployments = [
        BFAhvVmDeployment,
        BFAwsVmDeployment,
        BFAzureVmDeployment,
        BFGcpVmDeployment2,
    ]

    @action
    def test_profile_action():
        """Sample description for a profile action"""
        CalmTask.Exec.ssh(name="Task5", script='echo "Hello"', target=ref(AhvVmService))


class AhvBlueprint(Blueprint):
    """Sample Bp that used multi-cloud vms"""

    credentials = [Centos]
    services = [AhvVmService, AwsVmService, AzureVmService, GcpVmService]
    packages = [AhvVmPackage, Era_Disk, AwsVmPackage, AzureVmPackage, GcpVmPackage]
    substrates = [AhvVmSubstrate, AwsVmSubstrate, AzureVmSubstrate, GcpVmSubstrate]
    profiles = [AhvVmProfile]
