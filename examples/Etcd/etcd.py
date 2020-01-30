"""
CALM DSL Etcd Blueprint

"""

from calm.dsl.builtins import ref, basic_cred, CalmTask
from calm.dsl.builtins import action
from calm.dsl.builtins import CalmVariable
from calm.dsl.builtins import Service, Package, Substrate
from calm.dsl.builtins import Deployment, Profile, Blueprint
from calm.dsl.builtins import vm_disk_package
from calm.dsl.builtins import read_local_file
from calm.dsl.builtins import read_ahv_spec


# Path to read ssh private key
CENTOS_KEY = read_local_file("secrets/private_key")
# Default credential
DefaultCred = basic_cred("centos", CENTOS_KEY, name="CENTOS", type="KEY", default=True)
# Downloadable images for AHV & VMware
AHV_CENTOS_76 = vm_disk_package(name="AHV_CENTOS_76", config_file="specs/image_config/ahv_centos.yaml")


class Etcd(Service):
    """Etcd service"""

    CREATE_VOLUME = CalmVariable.WithOptions.Predefined.string(["yes", "no"], default="yes", is_mandatory=True, runtime=True)  # noqa
    SSL_ON = CalmVariable.WithOptions.Predefined.string(["yes", "no"], default="yes", is_mandatory=True, runtime=True)  # noqa

    @action
    def __start__():
        CalmTask.Exec.ssh(name="Start", filename="scripts/Etcd_Start.sh")


class EtcdPackage(Package):
    """
    Package install for Etcd
    Install Etcd service
    """

    services = [ref(Etcd)]

    @action
    def __install__():
        CalmTask.Exec.ssh(name="Prerequisites", filename="scripts/Prerequisites.sh")
        CalmTask.Exec.ssh(name="Install and Configure Etcd", filename="scripts/Etcd_Install.sh")
        CalmTask.Exec.ssh(name="Etcd Validation", filename="scripts/Etcd_Validation.sh")


class AHV_Etcd(Substrate):
    """
    Etcd AHV Spec
    Default 2 CPU & 2 GB of memory
    6 disks (3 X etcd data & 3 X container data)
    """

    provider_spec = read_ahv_spec(
        "specs/substrate/ahv_spec_centos.yaml", disk_packages={1: AHV_CENTOS_76}
    )


class EtcdDeployment(Deployment):
    """
    Etcd deployment
    default min_replicas - 3
    default max_replicas - 5
    """

    packages = [ref(EtcdPackage)]
    substrate = ref(AHV_Etcd)
    min_replicas = "3"
    max_replicas = "5"


class Nutanix(Profile):
    """
    Etcd Nutanix Application profile.
    """

    ETCD_VERSION = CalmVariable.Simple(
        "v3.3.15",
        label="Etcd cluster version",
        regex=r"^v3\.[0-9]\.[0-9]?[0-9]$",
        validate_regex=True,
        is_mandatory=True,
        runtime=True,
    )

    deployments = [EtcdDeployment]


class EtcdDslBlueprint(Blueprint):
    """Etcd blueprint"""

    profiles = [Nutanix]
    services = [Etcd]
    substrates = [AHV_Etcd]
    packages = [EtcdPackage, AHV_CENTOS_76]
    credentials = [DefaultCred]


def main():
    print(EtcdDslBlueprint.json_dumps(pprint=True))


if __name__ == "__main__":
    main()
