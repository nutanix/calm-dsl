import json

from calm.dsl.builtins import AhvVmDisk, AhvVmNic
from calm.dsl.builtins import AhvVmResources, AhvVm

from calm.dsl.builtins import ref, basic_cred, CalmVariable, CalmTask, action
from calm.dsl.builtins import Service, Package, Substrate
from calm.dsl.builtins import Deployment, Profile, Blueprint
from calm.dsl.builtins import read_local_file, read_spec
from calm.dsl.builtins import readiness_probe, Ref, Metadata
from calm.dsl.builtins import AppEdit, PatchField, AhvUpdateConfigAttrs

CRED_USERNAME = read_local_file(".tests/username")
CRED_PASSWORD = read_local_file(".tests/password")
DNS_SERVER = read_local_file(".tests/dns_server")

DSL_CONFIG = json.loads(read_local_file(".tests/config.json"))
CENTOS_CI = DSL_CONFIG["AHV"]["IMAGES"]["DISK"]["CENTOS_7_CLOUD_INIT"]
SUBNET = DSL_CONFIG["ACCOUNTS"]["NUTANIX_PC"][0]["SUBNETS"][0]["NAME"]
CLUSTER = DSL_CONFIG["ACCOUNTS"]["NUTANIX_PC"][0]["SUBNETS"][0]["CLUSTER"]
NETWORK1 = DSL_CONFIG["AHV"]["NETWORK"]["VLAN1211"]

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
    vCPUs = 1
    cores_per_vCPU = 1
    disks = [
        AhvVmDisk(CENTOS_CI, bootable=True),
        AhvVmDisk.Disk.Pci.allocateOnStorageContainer(4),
        AhvVmDisk.Disk.Pci.allocateOnStorageContainer(6),
        AhvVmDisk.Disk.Pci.allocateOnStorageContainer(8),
    ]
    nics = [
        AhvVmNic(NETWORK1),
        AhvVmNic(NETWORK1),
        AhvVmNic(NETWORK1),
    ]
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


class AhvUpdateAttrs(AhvUpdateConfigAttrs):
    """AHV VM update attributes"""

    memory = PatchField.Ahv.vcpu(
        value="2", operation="equal", min_val=1, max_val=10, editable=True
    )
    vcpu = PatchField.Ahv.vcpu(
        value="2", operation="equal", min_val=1, max_val=10, editable=True
    )
    numsocket = PatchField.Ahv.vcpu(
        value="2", operation="equal", min_val=1, max_val=10, editable=True
    )

    disk_delete = True
    categories_delete = True
    nic_delete = True
    categories_add = True

    nics = [
        PatchField.Ahv.Nics.add(
            AhvVmNic(NETWORK1),
            editable=True,
        ),
    ]

    disks = [
        PatchField.Ahv.Disks.modify(
            index=2, editable=True, operation="modify", value="3", min_val=1, max_val=10
        ),
        PatchField.Ahv.Disks.modify(
            index=3, editable=True, operation="modify", value="5", min_val=1, max_val=10
        ),
    ]

    categories = [
        PatchField.Ahv.Category.add({"TemplateType": "Vm"}),
        PatchField.Ahv.Category.delete({"AppFamily": "Demo"}),
    ]


class DefaultProfile(Profile):
    """Sample application profile with variables"""

    nameserver = CalmVariable.Simple(DNS_SERVER, label="Local DNS resolver")
    foo1 = CalmVariable.Simple("bar1", runtime=True)
    foo2 = CalmVariable.Simple("bar2", runtime=True)

    deployments = [AhvDeployment]

    patch_list = [
        AppEdit.UpdateConfig(
            "patch_update", target=ref(AhvDeployment), patch_attrs=AhvUpdateAttrs
        )
    ]


class TestRuntime(Blueprint):

    credentials = [DefaultCred]
    services = [AhvService]
    packages = [AhvPackage]
    substrates = [AhvSubstrate]
    profiles = [DefaultProfile]


class BpMetadata(Metadata):

    project = Ref.Project(PROJECT_NAME)
