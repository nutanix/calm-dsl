from calm.dsl.builtins import ref, basic_cred, CalmVariable, CalmTask, action
from calm.dsl.builtins import Service, Package, Substrate
from calm.dsl.builtins import Deployment, Profile, Blueprint
from calm.dsl.builtins import read_provider_spec


class SampleService(Service):
    """Sample service"""

    ENV = CalmVariable.Simple("DEV")


class SamplePackage(Package):
    """Example package with variables, install tasks and link to service"""

    foo = CalmVariable.Simple("bar")
    services = [ref(SampleService)]

    @action
    def __install__():
        CalmTask.Exec.ssh(name="Task1", script="echo @@{foo}@@")


class SampleVM(Substrate):
    """Azure VM config given by reading a spec file"""

    os_type = "Windows"
    provider_type = "GCP_VM"
    provider_spec = read_provider_spec("provider_spec.yaml")


class SampleDeployment(Deployment):
    """Sample deployment pulling in service and substrate references"""

    packages = [ref(SamplePackage)]
    substrate = ref(SampleVM)


class DefaultProfile(Profile):
    """Sample application profile with variables"""

    nameserver = CalmVariable.Simple("10.40.64.15", label="Local DNS resolver")
    foo1 = CalmVariable.Simple("bar1", runtime=True)
    foo2 = CalmVariable.Simple("bar2", runtime=True)

    deployments = [SampleDeployment]


class SampleBlueprint(Blueprint):
    """Sample blueprint"""

    credentials = [basic_cred("username", "password", default=True)]
    services = [SampleService]
    packages = [SamplePackage]
    substrates = [SampleVM]
    profiles = [DefaultProfile]
