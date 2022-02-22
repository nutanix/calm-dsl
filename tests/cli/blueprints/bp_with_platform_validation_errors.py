from calm.dsl.builtins import ref, basic_cred, read_local_file, read_provider_spec
from calm.dsl.builtins import AhvVmResources, AhvVm
from calm.dsl.builtins import (
    Substrate,
    Deployment,
    Service,
    Package,
    Profile,
    Blueprint,
)


CRED_USERNAME = read_local_file(".tests/username")
CRED_PASSWORD = read_local_file(".tests/password")
DefaultCred = basic_cred(CRED_USERNAME, CRED_PASSWORD, name="credential", default=True)


class AHVService(Service):
    name = "AHVService"


class AHVPackage(Package):
    services = [ref(AHVService)]


class AHVResources(AhvVmResources):
    memory = 2
    vCPUs = 1
    cores_per_vCPU = 1


class AHVVm(AhvVm):
    resources = AHVResources


class AHVSubstrate(Substrate):
    os_type = "Linux"
    provider_type = "AHV_VM"
    provider_spec = AHVVm


class AHVDeployment(Deployment):
    packages = [ref(AHVPackage)]
    substrate = ref(AHVSubstrate)


class VMWService(Service):
    name = "VMWService"


class VMWPackage(Package):
    services = [ref(VMWService)]


class VMWSubstrate(Substrate):
    os_type = "Linux"
    provider_type = "VMWARE_VM"
    provider_spec = read_provider_spec("../../cli/blueprints/provider_spec.yaml")


class VMWDeployment(Deployment):
    packages = [ref(VMWPackage)]
    substrate = ref(VMWSubstrate)


class DefaultProfile(Profile):
    deployments = [AHVDeployment, VMWDeployment]


class AHVBlueprint(Blueprint):
    """Blueprint"""

    credentials = [DefaultCred]
    services = [AHVService, VMWService]
    packages = [AHVPackage, VMWPackage]
    substrates = [AHVSubstrate, VMWSubstrate]
    profiles = [DefaultProfile]
