from calm.dsl.builtins import ref, basic_cred, CalmVariable, CalmTask, action
from calm.dsl.builtins import Service, Package, Substrate
from calm.dsl.builtins import Deployment, Profile, Blueprint
from calm.dsl.builtins import read_provider_spec, read_local_file


AZURE_VM_PASSWD = read_local_file("passwd")


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


class AzureVM(Substrate):
    """Azure VM config given by reading a spec file"""

    provider_type = "AZURE_VM"
    provider_spec = read_provider_spec("azure_spec.yaml")


class SampleDeployment(Deployment):
    """Sample deployment pulling in service and substrate references"""

    packages = [ref(SamplePackage)]
    substrate = ref(AzureVM)


class DefaultProfile(Profile):
    """Sample application profile with variables"""

    nameserver = CalmVariable.Simple("10.40.64.15", label="Local DNS resolver")
    foo1 = CalmVariable.Simple("bar1", runtime=True)
    foo2 = CalmVariable.Simple("bar2", runtime=True)

    deployments = [SampleDeployment]


class AzureBlueprint(Blueprint):
    """Sample azure blueprint"""

    credentials = [basic_cred("azureusername", AZURE_VM_PASSWD, default=True)]
    services = [SampleService]
    packages = [SamplePackage]
    substrates = [AzureVM]
    profiles = [DefaultProfile]


def main():
    print(AzureBlueprint.json_dumps(pprint=True))


if __name__ == "__main__":
    main()
