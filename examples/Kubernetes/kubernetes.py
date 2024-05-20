"""
Calm DSL Kubernetes Blueprint

"""

from calm.dsl.builtins import ref, basic_cred, CalmTask
from calm.dsl.builtins import action, parallel
from calm.dsl.builtins import CalmVariable
from calm.dsl.builtins import Service, Package, Substrate
from calm.dsl.builtins import Deployment, Profile, Blueprint
from calm.dsl.builtins import read_provider_spec, read_local_file


CENTOS_PASSWD = read_local_file(".tests/password")


class Master(Service):
    """Kubernetes master service"""

    VERSION = CalmVariable.Simple("")  # noqa

    @action
    def __create__():
        CalmTask.Exec.ssh(name="Dashboard", filename="scripts/Master07.sh")
        CalmTask.Exec.ssh(name="HELM", filename="scripts/Master08.sh")
        CalmTask.Exec.ssh(name="MetricsServer", filename="scripts/Master09.sh")

    @action
    def __start__():
        CalmTask.Exec.ssh(name="Start", filename="scripts/Master10.sh")


class Worker(Service):
    """Kubernetes Worker service"""

    VERSION = CalmVariable.Simple("")  # noqa

    @action
    def __start__():
        CalmTask.Exec.ssh(name="Start", filename="scripts/Worker03.sh")


class MasterPackage(Package):
    """
    Package install for master
    Install Etcd, Docker & Kubernetes Master Services
    Configures kubernetes network using flannel, calico or canal CNI plugins
    """

    services = [ref(Master)]

    @action
    def __install__():
        CalmTask.SetVariable.escript.py3(
            name="Set Kubernetes Version",
            script="print ('VERSION=@@{KUBE_VERSION}@@')",
            variables=["VERSION"],
        )
        CalmTask.Exec.ssh(
            name="ETCD Docker Kubelet Install", filename="scripts/Master01.sh"
        )
        CalmTask.Exec.ssh(name="Generate Certs", filename="scripts/Master02.sh")
        CalmTask.Exec.ssh(name="Configure Services", filename="scripts/Master03.sh")
        CalmTask.Exec.ssh(name="Add User Roles", filename="scripts/Master04.sh")
        CalmTask.Exec.ssh(name="Network Configuration", filename="scripts/Master05.sh")
        CalmTask.Exec.ssh(name="DNS Configuration", filename="scripts/Master06.sh")


class WorkerPackage(Package):
    """
    Package install for worker
    Install Docker & Kubernetes Worker Services
    """

    services = [ref(Worker)]

    @action
    def __install__():
        CalmTask.SetVariable.escript.py3(
            name="Set Kubernetes Version",
            script="print ('VERSION=@@{KUBE_VERSION}@@')",
            variables=["VERSION"],
        )
        CalmTask.Exec.ssh(name="Docker Kubelet Install", filename="scripts/Worker01.sh")
        CalmTask.Exec.ssh(name="Get Certs", filename="scripts/Worker02.sh")

    @action
    def __uninstall__():
        CalmTask.Exec.ssh(name="Remote Node", filename="scripts/Worker05.sh")


class AHV_Master(Substrate):
    """
    Master AHV Spec
    Default 2 CPU & 2 GB of memory
    6 disks (3 X etcd data & 3 X container data)
    """

    provider_spec = read_provider_spec("ahv_spec_master.yaml")


class AHV_Worker(Substrate):
    """
    Worker AHV Spec
    Default 2 CPU & 2 GB of memory
    3 disks (3 X container data)
    """

    provider_spec = read_provider_spec("ahv_spec_worker.yaml")


class MasterDeployment(Deployment):
    """
    Master deployment
    default min_replicas - 3
    default max_replicas - 5
    """

    packages = [ref(MasterPackage)]
    substrate = ref(AHV_Master)
    min_replicas = "3"
    max_replicas = "5"


class WorkerDeployment(Deployment):
    """
    Worker deployment
    default min_replicas - 2
    default max_replicas - 5
    """

    packages = [ref(WorkerPackage)]
    substrate = ref(AHV_Worker)
    min_replicas = "2"
    max_replicas = "5"


class Nutanix(Profile):
    """
    Kubernetes Nutanix Application profile.
    Actions Supported:
    - Upgrade
    - ScaleOut
    - ScaleIn
    """

    KUBE_CLUSTER_NAME = CalmVariable.Simple(
        "ahv-kubenetes-cluster",
        label="Kubernetes cluster name",
        is_mandatory=True,
        runtime=True,
    )
    KUBE_VERSION = CalmVariable.Simple(
        "v1.12.8",
        label="Kubernetes cluster version",
        regex=r"^v1\.[0-9]?[0-9]\.[0-9]?[0-9]$",
        validate_regex=True,
        is_mandatory=True,
        runtime=True,
    )
    DOCKER_VERSION = CalmVariable.WithOptions.Predefined.string(
        [
            "17.03.3.ce",
            "17.06.2.ce",
            "17.09.1.ce",
            "17.12.1.ce",
            "18.03.1.ce",
            "18.06.3.ce",
        ],
        default="17.03.3.ce",
        label="Docker version",
        is_mandatory=True,
        runtime=True,
    )
    KUBE_CLUSTER_SUBNET = CalmVariable.Simple(
        "10.200.0.0/16",
        label="Kubernetes cluster subnet cidr",
        regex=r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\/\d{1,2}$",
        validate_regex=True,
        is_mandatory=True,
        runtime=True,
    )
    KUBE_SERVICE_SUBNET = CalmVariable.Simple(
        "10.32.0.0/24",
        label="Kubernetes service subnet cidr",
        regex=r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\/\d{1,2}$",
        validate_regex=True,
        is_mandatory=True,
        runtime=True,
    )
    KUBE_DNS_IP = CalmVariable.Simple(
        "10.32.0.10",
        label="Kube DNS IP",
        regex=r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$",
        validate_regex=True,
        is_mandatory=True,
        runtime=True,
    )
    KUBE_CNI_PLUGIN = CalmVariable.WithOptions.Predefined.string(
        ["flannel", "canal", "calico"],
        default="flannel",
        label="Kubernetes CNI plugin type",
        is_mandatory=True,
        runtime=True,
    )

    deployments = [MasterDeployment, WorkerDeployment]

    @action
    def Upgrade():
        KUBE_VERSION_NEW = CalmVariable.Simple.string(  # noqa
            "v1.13.6",
            label="Kubernetes cluster version",
            regex=r"^v1\.[0-9]?[0-9]\.[0-9]?[0-9]$",
            validate_regex=True,
            is_mandatory=True,
            runtime=True,
        )

        with parallel():
            CalmTask.SetVariable.escript.py3(
                name="Set Version Master",
                script="print ('VERSION=@@{KUBE_VERSION_NEW}@@')",
                variables=["VERSION"],
                target=ref(Master),
            )
            CalmTask.SetVariable.escript.py3(
                name="Set Version Slave",
                script="print ('VERSION=@@{KUBE_VERSION_NEW}@@')",
                variables=["VERSION"],
                target=ref(Worker),
            )
        with parallel():
            CalmTask.Exec.ssh(
                name="Upgrade Master",
                filename="scripts/Master11.sh",
                target=ref(Master),
            )
            CalmTask.Exec.ssh(
                name="Upgrade Minion",
                filename="scripts/Worker04.sh",
                target=ref(Worker),
            )
        CalmTask.Exec.ssh(
            name="RestartServices", filename="scripts/Master12.sh", target=ref(Master)
        )

    @action
    def ScaleOut():
        COUNT = CalmVariable.Simple.int("1", is_mandatory=True, runtime=True)  # noqa
        CalmTask.Scaling.scale_out(
            "@@{COUNT}@@", target=ref(WorkerDeployment), name="Scale out Worker"
        )
        CalmTask.Exec.ssh(
            name="Set Hosts file", filename="scripts/Master13.sh", target=ref(Master)
        )

    @action
    def ScaleIn():
        COUNT = CalmVariable.Simple.int("1", is_mandatory=True, runtime=True)  # noqa
        CalmTask.Scaling.scale_in(
            "@@{COUNT}@@", target=ref(WorkerDeployment), name="Scale in Worker"
        )
        CalmTask.Exec.ssh(
            name="Set Hosts file", filename="scripts/Master13.sh", target=ref(Master)
        )


class KubernetesDslBlueprint(Blueprint):
    """Kubernetes blueprint"""

    profiles = [Nutanix]
    services = [Master, Worker]
    substrates = [AHV_Master, AHV_Worker]
    packages = [MasterPackage, WorkerPackage]
    credentials = [basic_cred("centos", CENTOS_PASSWD, name="CENTOS", default=True)]


def main():
    print(KubernetesDslBlueprint.json_dumps(pprint=True))


if __name__ == "__main__":
    main()
