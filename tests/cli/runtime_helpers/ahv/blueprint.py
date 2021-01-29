import json
from tests.ahv_vm.test_ahv_multivm import CENTOS_CI

from calm.dsl.builtins import AhvVmDisk, AhvVmNic
from calm.dsl.builtins import AhvVmResources, AhvVm

from calm.dsl.builtins import ref, basic_cred, CalmVariable, CalmTask, action
from calm.dsl.builtins import Service, Package, Substrate
from calm.dsl.builtins import Deployment, Profile, Blueprint
from calm.dsl.builtins import read_local_file, read_spec
from calm.dsl.builtins import readiness_probe, Ref, Metadata

CRED_USERNAME = read_local_file(".tests/username")
CRED_PASSWORD = read_local_file(".tests/password")
DNS_SERVER = read_local_file(".tests/dns_server")

DSL_CONFIG = json.loads(read_local_file(".tests/config.json"))
CENTOS_CI = DSL_CONFIG["AHV"]["IMAGES"]["DISK"]["CENTOS_7_CLOUD_INIT"]
NETWORK1 = DSL_CONFIG["AHV"]["NETWORK"]["VLAN1211"]  # TODO change network constants

# projects
PROJECT = DSL_CONFIG["PROJECTS"]["PROJECT1"]
PROJECT_NAME = PROJECT["NAME"]

DefaultCred = basic_cred(
    CRED_USERNAME,
    CRED_PASSWORD,
    name="default cred",
    default=True,
    editables={"username": True, "secret": True},
)


class AhvService(Service):
    """Sample mysql service"""

    ENV = CalmVariable.Simple("DEV")


class AhvPackage(Package):
    """Example package with variables, install tasks and link to service"""

    foo = CalmVariable.Simple("bar")
    services = [ref(AhvService)]


class MyAhvVmResources(AhvVmResources):

    memory = 4
    vCPUs = 2
    cores_per_vCPU = 1
    disks = [
        AhvVmDisk(CENTOS_CI, bootable=True),
        AhvVmDisk.Disk.Pci.allocateOnStorageContainer(12),
    ]
    nics = [AhvVmNic(NETWORK1)]

    serial_ports = {0: False, 1: False, 2: True, 3: True}


class MyAhvVm(AhvVm):

    resources = MyAhvVmResources
    categories = {"AppFamily": "Backup", "AppType": "Default"}


class AhvSubstrate(Substrate):
    """AHV VM config given by reading a spec file"""

    provider_spec = MyAhvVm
    provider_spec_editables = read_spec("specs/ahv_substrate_editable.yaml")

    readiness_probe = readiness_probe(
        connection_type="SSH",
        credential=ref(DefaultCred),
        disabled=True,
        editables_list=["connection_port", "retries"],
        timeout_secs="60",
        retries="5",
    )


class AhvDeployment(Deployment):
    """Sample deployment pulling in service and substrate references"""

    packages = [ref(AhvPackage)]
    substrate = ref(AhvSubstrate)
    editables = {"min_replicas": True, "default_replicas": True, "max_replicas": True}


class DefaultProfile(Profile):
    """Sample application profile with variables"""

    nameserver = CalmVariable.Simple(DNS_SERVER, label="Local DNS resolver")
    foo1 = CalmVariable.Simple("bar1", runtime=True)
    foo2 = CalmVariable.Simple("bar2", runtime=True)

    deployments = [AhvDeployment]

    @action
    def test_profile_action():
        """Sample description for a profile action"""
        var_run = CalmVariable.Simple(  # Noqa
            "mail",
            runtime=True,
        )
        var_nor = CalmVariable.Simple("efg", runtime=False)  # Noqa
        var_secret = CalmVariable.Simple.Secret(  # Noqa
            "secret_var_val",
            runtime=True,
        )
        var_with_choices = CalmVariable.WithOptions(  # Noqa
            ["mail1", "mail2"],
            default="mail1",
            runtime=True,
        )
        CalmTask.Exec.ssh(name="Task5", script='echo "Hello"', target=ref(AhvService))
        CalmTask.Exec.ssh(
            name="PrintActionVarTask",
            script="echo @@{var_run}@@\necho @@{var_nor}@@\necho @@{var_secret}@@\necho @@{var_with_choices}@@",
            target=ref(AhvService),
        )


class TestRuntime(Blueprint):

    credentials = [DefaultCred]
    services = [AhvService]
    packages = [AhvPackage]
    substrates = [AhvSubstrate]
    profiles = [DefaultProfile]


class BpMetadata(Metadata):

    project = Ref.Project(PROJECT_NAME)
