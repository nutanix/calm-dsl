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


def get_vpc_project(config):
    project_name = "default"
    vpc_enabled = config.get("IS_VPC_ENABLED", False)
    if not vpc_enabled:
        return project_name

    project_name = (
        config.get("VPC_PROJECTS", {}).get("PROJECT1", {}).get("NAME", "default")
    )


def get_local_az_overlay_details_from_dsl_config(config):
    networks = config["ACCOUNTS"]["NUTANIX_PC"]
    local_az_account = None
    for account in networks:
        if account.get("NAME") == "NTNX_LOCAL_AZ":
            local_az_account = account
            break
    overlay_subnets_list = local_az_account.get("OVERLAY_SUBNETS", [])
    vlan_subnets_list = local_az_account.get("SUBNETS", [])

    cluster = ""
    vpc = ""
    overlay_subnet = ""

    for subnet in overlay_subnets_list:
        if subnet["NAME"] == "vpc_subnet_1" and subnet["VPC"] == "vpc_name_1":
            overlay_subnet = subnet["NAME"]
            vpc = subnet["VPC"]

    for subnet in vlan_subnets_list:
        if subnet["NAME"] == config["AHV"]["NETWORK"]["VLAN1211"]:
            cluster = subnet["CLUSTER"]
            break
    return overlay_subnet, vpc, cluster


NETWORK1, VPC1, CLUSTER1 = get_local_az_overlay_details_from_dsl_config(DSL_CONFIG)
VPC_PROJECT = get_vpc_project(DSL_CONFIG)

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
        AhvVmNic(NETWORK1, vpc=VPC1),
        AhvVmNic(NETWORK1, vpc=VPC1),
        AhvVmNic(NETWORK1, vpc=VPC1),
    ]
    serial_ports = {0: False, 1: False, 2: True, 3: True}


class MyAhvVm(AhvVm):

    resources = MyAhvVmResources
    categories = {"AppFamily": "Backup", "AppType": "Default"}
    cluster = Ref.Cluster(name=CLUSTER1)


class AhvSubstrate(Substrate):
    """AHV VM config given by reading a spec file"""

    provider_spec = MyAhvVm
    provider_spec_editables = read_spec("specs/ahv_overlay_substrate_editable.yaml")

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
            AhvVmNic(NETWORK1, vpc=VPC1),
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


class TestVPCRuntime(Blueprint):

    credentials = [DefaultCred]
    services = [AhvService]
    packages = [AhvPackage]
    substrates = [AhvSubstrate]
    profiles = [DefaultProfile]


class BpMetadata(Metadata):
    project = Ref.Project(VPC_PROJECT)
