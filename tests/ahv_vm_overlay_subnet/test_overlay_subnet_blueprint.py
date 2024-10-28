import json
import os

from calm.dsl.builtins import Service, Package, Substrate
from calm.dsl.builtins import Deployment, Profile, Blueprint, Metadata
from calm.dsl.builtins import CalmVariable as Variable
from calm.dsl.builtins import CalmTask as Task
from calm.dsl.builtins import action, parallel, ref, basic_cred
from calm.dsl.builtins import read_local_file
from calm.dsl.builtins import vm_disk_package, AhvVmDisk, AhvVmNic
from calm.dsl.builtins import AhvVmGC, AhvVmResources, AhvVm, Ref

from tests.utils import get_vpc_project, get_local_az_overlay_details_from_dsl_config

DSL_CONFIG = json.loads(read_local_file(".tests/config.json"))
VPC_PROJECT = get_vpc_project(DSL_CONFIG)

ACCOUNT_NAME = DSL_CONFIG["ACCOUNTS"]["NTNX_LOCAL_AZ"]["NAME"]
NETWORK1, VPC1, CLUSTER1 = get_local_az_overlay_details_from_dsl_config(DSL_CONFIG)

# SSH Credentials
CENTOS_USER = "centos"
CENTOS_KEY = read_local_file(".tests/keys/centos")
CENTOS_PUBLIC_KEY = read_local_file(".tests/keys/centos_pub")
CentosCred = basic_cred(
    CENTOS_USER,
    CENTOS_KEY,
    name="Centos",
    type="KEY",
    default=True,
)

# OS Image details for VM
CENTOS_IMAGE_SOURCE = "http://download.nutanix.com/calm/CentOS-7-x86_64-1810.qcow2"
CentosPackage = vm_disk_package(
    name="centos_disk",
    config={"image": {"source": CENTOS_IMAGE_SOURCE}},
)


class HelloService(Service):
    """Sample Service"""

    # Custom service actions
    @action
    def custom_action_1():
        """Sample service action"""

        # Step 1
        Task.Exec.ssh(name="Task11", script='echo "Hello"')

        # Step 2
        Task.Exec.ssh(name="Task12", script='echo "Hello again"')


class HelloPackage(Package):
    """Sample Package"""

    # Services created by installing this Package
    services = [ref(HelloService)]


class HelloVmResources(AhvVmResources):

    memory = 4
    vCPUs = 2
    cores_per_vCPU = 1
    disks = [
        AhvVmDisk.Disk.Scsi.cloneFromVMDiskPackage(CentosPackage, bootable=True),
    ]
    # TODO replace vpc, nic name from config
    nics = [AhvVmNic.NormalNic.ingress(NETWORK1, vpc=VPC1)]
    # nics = [AhvVmNic.DirectNic.ingress(subnet="vlan.800", cluster="auto_cluster_prod_1a619308826b")]

    guest_customization = AhvVmGC.CloudInit(
        config={
            "users": [
                {
                    "name": CENTOS_USER,
                    "ssh-authorized-keys": [CENTOS_PUBLIC_KEY],
                    "sudo": ["ALL=(ALL) NOPASSWD:ALL"],
                }
            ]
        }
    )


class HelloVm(AhvVm):

    resources = HelloVmResources
    # TODO - replace cluster name from config
    cluster = Ref.Cluster(name=CLUSTER1)
    categories = {"AppFamily": "Demo", "AppType": "Default"}


class HelloSubstrate(Substrate):
    """AHV VM Substrate"""

    provider_type = "AHV_VM"
    provider_spec = HelloVm
    account = Ref.Account(name=ACCOUNT_NAME)

    # Substrate Actions
    @action
    def __pre_create__():

        # Step 1
        Task.Exec.escript.py3(
            name="Task1", script="print ('Pre Create task runs before VM is created')"
        )

    @action
    def __post_delete__():

        # Step 1
        Task.Exec.escript.py3(
            name="Task1", script="print ('Post delete task runs after VM is deleted')"
        )


class HelloDeployment(Deployment):
    """Sample Deployment"""

    packages = [ref(HelloPackage)]
    substrate = ref(HelloSubstrate)


class HelloProfile(Profile):

    # Deployments under this profile
    deployments = [HelloDeployment]


class DSLDemo(Blueprint):
    """Sample blueprint for Hello app using AHV VM"""

    credentials = [CentosCred]
    services = [HelloService]
    packages = [HelloPackage, CentosPackage]
    substrates = [HelloSubstrate]
    profiles = [HelloProfile]


class BpMetadata(Metadata):
    project = Ref.Project(VPC_PROJECT["name"])
