import json

from calm.dsl.builtins import Service, Package, Substrate
from calm.dsl.builtins import Deployment, Profile, Blueprint, Metadata
from calm.dsl.builtins import ref, basic_cred
from calm.dsl.builtins import read_local_file
from calm.dsl.builtins import vm_disk_package, AhvVmDisk, AhvVmNic
from calm.dsl.builtins import AhvVmGC, AhvVmResources, AhvVm
from calm.dsl.builtins import AhvVmGC, AhvVmResources, AhvVm, Ref


DSL_CONFIG = json.loads(read_local_file(".tests/config.json"))

PROJECT = DSL_CONFIG["PROJECTS"]["PROJECT1"]
PROJECT_NAME = PROJECT["NAME"]
NTNX_LOCAL_ACCOUNT = DSL_CONFIG["ACCOUNTS"]["NTNX_LOCAL_AZ"]
SUBNET_NAME = NTNX_LOCAL_ACCOUNT["SUBNETS"][1]["NAME"]
CLUSTER_NAME = NTNX_LOCAL_ACCOUNT["SUBNETS"][1]["CLUSTER"]

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
    pass


class HelloPackage(Package):
    services = [ref(HelloService)]


class HelloVmResources(AhvVmResources):

    memory = 4
    vCPUs = 2
    cores_per_vCPU = 1
    disks = [
        AhvVmDisk.Disk.Scsi.cloneFromVMDiskPackage(CentosPackage, bootable=True),
    ]
    nics = [AhvVmNic.DirectNic.ingress(subnet=SUBNET_NAME, cluster=CLUSTER_NAME)]

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


class HelloSubstrate(Substrate):
    """AHV VM Substrate"""

    provider_type = "AHV_VM"
    provider_spec = HelloVm


class HelloDeployment(Deployment):
    """Sample Deployment"""

    packages = [ref(HelloPackage)]
    substrate = ref(HelloSubstrate)


class HelloProfile(Profile):
    deployments = [HelloDeployment]


class Hello(Blueprint):
    """Sample blueprint for Hello app using AHV VM"""

    credentials = [CentosCred]
    services = [HelloService]
    packages = [HelloPackage, CentosPackage]
    substrates = [HelloSubstrate]
    profiles = [HelloProfile]


class BpMetadata(Metadata):
    project = Ref.Project(PROJECT_NAME)
