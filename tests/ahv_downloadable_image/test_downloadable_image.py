from calm.dsl.builtins import ref, basic_cred, CalmVariable, CalmTask, action
from calm.dsl.builtins import Service, Package, Substrate
from calm.dsl.builtins import Deployment, Profile, Blueprint
from calm.dsl.builtins import read_ahv_spec, read_local_file
from calm.dsl.builtins import vm_disk_package


NAMESERVER = read_local_file(".tests/nameserver")
CRED_USERNAME = read_local_file(".tests/username")
CRED_PASSWORD = read_local_file(".tests/password")


class MySQLService(Service):
    """Sample mysql service"""

    ENV = CalmVariable.Simple("DEV")


class MySQLPackage(Package):
    """Example package with variables, install tasks and link to service"""

    foo = CalmVariable.Simple("bar")
    services = [ref(MySQLService)]

    @action
    def __install__():
        CalmTask.Exec.ssh(name="Task1", script="echo @@{foo}@@")


Virtio = vm_disk_package(name="era", config_file="specs/virtio_image_config.yaml")


class AHVVMforMySQL(Substrate):
    """AHV VM config given by reading a spec file"""

    provider_spec = read_ahv_spec(
        "specs/ahv_provider_spec.yaml", disk_packages={1: Virtio}
    )


class MySQLDeployment(Deployment):
    """Sample deployment pulling in service and substrate references"""

    packages = [ref(MySQLPackage)]
    substrate = ref(AHVVMforMySQL)


class DefaultProfile(Profile):
    """Sample application profile with variables"""

    nameserver = CalmVariable.Simple(NAMESERVER, label="Local DNS resolver")
    foo1 = CalmVariable.Simple("bar1", runtime=True)
    foo2 = CalmVariable.Simple("bar2", runtime=True)

    deployments = [MySQLDeployment]

    @action
    def test_profile_action():
        """Sample description for a profile action"""
        CalmTask.Exec.ssh(name="Task5", script='echo "Hello"', target=ref(MySQLService))


class DownloadablImageBp(Blueprint):
    """Downloadable Image demo"""

    credentials = [basic_cred(CRED_USERNAME, CRED_PASSWORD, default=True)]
    services = [MySQLService]
    packages = [MySQLPackage, Virtio]
    substrates = [AHVVMforMySQL]
    profiles = [DefaultProfile]


def main():
    print(DownloadablImageBp.json_dumps(pprint=True))


if __name__ == "__main__":
    main()
