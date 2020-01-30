"""
CALM DSL Etcd Blueprint

"""

from calm.dsl.builtins import ref, basic_cred, CalmTask
from calm.dsl.builtins import action, parallel
from calm.dsl.builtins import CalmVariable
from calm.dsl.builtins import Service, Package, Substrate
from calm.dsl.builtins import Deployment, Profile, Blueprint
from calm.dsl.builtins import read_provider_spec, read_local_file


CENTOS_PASSWD = read_local_file("passwd")


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

    provider_spec = read_provider_spec("ahv_spec.yaml")


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
    VLAN = CalmVariable.WithOptions.Predefined.string(["DMSAFSDHFLDSKJHFID-ADFSFDSLKFN_2394087", "DMSAFSDHFLDSKJHFID-ADFSFDSLKFN_239408"], default="DMSAFSDHFLDSKJHFID-ADFSFDSLKFN_2394087", label="Target Network VLAN", is_mandatory=True, runtime=True)  # noqa
    VLAN10 = CalmVariable.WithOptions.Predefined.string(["DMSAFSDHFLDSKJHFID-ADFSFDSLKFN_2394087", "DMSAFSDHFLDSKJHFID-ADFSFDSLKFN_239408"], default="DMSAFSDHFLDSKJHFID-ADFSFDSLKFN_2394087", label="Target Network VLAN", is_mandatory=True, runtime=True)  # noqa
    VLAN11 = CalmVariable.WithOptions.Predefined.string(["DMSAFSDHFLDSKJHFID-ADFSFDSLKFN_2394087", "DMSAFSDHFLDSKJHFID-ADFSFDSLKFN_239408"], default="DMSAFSDHFLDSKJHFID-ADFSFDSLKFN_2394087", label="Target Network VLAN", is_mandatory=True, runtime=True)  # noqa
    VLAN9 = CalmVariable.WithOptions.Predefined.string(["DMSAFSDHFLDSKJHFID-ADFSFDSLKFN_2394087", "DMSAFSDHFLDSKJHFID-ADFSFDSLKFN_239408"], default="DMSAFSDHFLDSKJHFID-ADFSFDSLKFN_2394087", label="Target Network VLAN", is_mandatory=True, runtime=True)  # noqa
    VLAN8 = CalmVariable.WithOptions.Predefined.string(["DMSAFSDHFLDSKJHFID-ADFSFDSLKFN_2394087", "DMSAFSDHFLDSKJHFID-ADFSFDSLKFN_239408"], default="DMSAFSDHFLDSKJHFID-ADFSFDSLKFN_2394087", label="Target Network VLAN", is_mandatory=True, runtime=True)  # noqa
    VLAN7 = CalmVariable.WithOptions.Predefined.string(["DMSAFSDHFLDSKJHFID-ADFSFDSLKFN_2394087", "DMSAFSDHFLDSKJHFID-ADFSFDSLKFN_239408"], default="DMSAFSDHFLDSKJHFID-ADFSFDSLKFN_2394087", label="Target Network VLAN", is_mandatory=True, runtime=True)  # noqa
    VLAN6 = CalmVariable.WithOptions.Predefined.string(["DMSAFSDHFLDSKJHFID-ADFSFDSLKFN_2394087", "DMSAFSDHFLDSKJHFID-ADFSFDSLKFN_239408"], default="DMSAFSDHFLDSKJHFID-ADFSFDSLKFN_2394087", label="Target Network VLAN", is_mandatory=True, runtime=True)  # noqa
    VLAN5 = CalmVariable.WithOptions.Predefined.string(["DMSAFSDHFLDSKJHFID-ADFSFDSLKFN_2394087", "DMSAFSDHFLDSKJHFID-ADFSFDSLKFN_239408"], default="DMSAFSDHFLDSKJHFID-ADFSFDSLKFN_2394087", label="Target Network VLAN", is_mandatory=True, runtime=True)  # noqa
    VLAN4 = CalmVariable.WithOptions.Predefined.string(["DMSAFSDHFLDSKJHFID-ADFSFDSLKFN_2394087", "DMSAFSDHFLDSKJHFID-ADFSFDSLKFN_239408"], default="DMSAFSDHFLDSKJHFID-ADFSFDSLKFN_2394087", label="Target Network VLAN", is_mandatory=True, runtime=True)  # noqa
    VLAN3 = CalmVariable.WithOptions.Predefined.string(["DMSAFSDHFLDSKJHFID-ADFSFDSLKFN_2394087", "DMSAFSDHFLDSKJHFID-ADFSFDSLKFN_239408"], default="DMSAFSDHFLDSKJHFID-ADFSFDSLKFN_2394087", label="Target Network VLAN", is_mandatory=True, runtime=True)  # noqa
    VLAN2 = CalmVariable.WithOptions.Predefined.string(["DMSAFSDHFLDSKJHFID-ADFSFDSLKFN_2394087", "DMSAFSDHFLDSKJHFID-ADFSFDSLKFN_239408"], default="DMSAFSDHFLDSKJHFID-ADFSFDSLKFN_2394087", label="Target Network VLAN", is_mandatory=True, runtime=True)  # noqa
    VLAN1 = CalmVariable.WithOptions.Predefined.string(["DMSAFSDHFLDSKJHFID-ADFSFDSLKFN_2394087", "DMSAFSDHFLDSKJHFID-ADFSFDSLKFN_239408"], default="DMSAFSDHFLDSKJHFID-ADFSFDSLKFN_2394087", label="Target Network VLAN", is_mandatory=True, runtime=True)  # noqa

    deployments = [EtcdDeployment]


class EtcdDslBlueprint(Blueprint):
    """Etcd blueprint"""

    profiles = [Nutanix]
    services = [Etcd]
    substrates = [AHV_Etcd]
    packages = [EtcdPackage]
    credentials = [basic_cred("centos", "nutanix/4u", name="CENTOS", default=True)]


def main():
    print(EtcdDslBlueprint.json_dumps(pprint=True))


if __name__ == "__main__":
    main()
