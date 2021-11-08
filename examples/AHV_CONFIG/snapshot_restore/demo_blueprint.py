import os

from calm.dsl.builtins import Service, Package, Substrate
from calm.dsl.builtins import Deployment, Profile, Blueprint
from calm.dsl.builtins import CalmVariable as Variable
from calm.dsl.builtins import CalmTask as Task
from calm.dsl.builtins import action, parallel, ref, basic_cred
from calm.dsl.builtins import read_local_file
from calm.dsl.builtins import vm_disk_package, AhvVmDisk, AhvVmNic
from calm.dsl.builtins import AhvVmGC, AhvVmResources, AhvVm
from calm.dsl.builtins import ref, Ref
from calm.dsl.builtins import AppProtection

# SSH Credentials
CENTOS_USER = "centos"
CENTOS_KEY = read_local_file(os.path.join("keys", "centos"))
CENTOS_PUBLIC_KEY = read_local_file(os.path.join("keys", "centos_pub"))
CentosCred = basic_cred(
    CENTOS_USER, CENTOS_KEY, name="Centos", type="KEY", default=True,
)

# OS Image details for VM
CENTOS_IMAGE_SOURCE = "http://download.nutanix.com/calm/CentOS-7-x86_64-1810.qcow2"
CentosPackage = vm_disk_package(
    name="centos_disk", config={"image": {"source": CENTOS_IMAGE_SOURCE}},
)


class HelloService(Service):
    """Sample Service"""

    # Service Actions
    @action
    def __create__():
        # Step 1
        Task.Exec.ssh(name="Task1", script="echo 'Service create in ENV'")


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
    nics = [AhvVmNic.DirectNic.ingress(subnet="nested_vms", cluster="cluster_1")]

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
    categories = {"AppFamily": "Demo", "AppType": "Default"}


class HelloSubstrate(Substrate):
    """AHV VM Substrate"""

    provider_type = "AHV_VM"
    provider_spec = HelloVm

    # Substrate Actions
    @action
    def __pre_create__():

        # Step 1
        Task.Exec.escript(
            name="Task1", script="print 'Pre Create task runs before VM is created'"
        )

    @action
    def __post_delete__():

        # Step 1
        Task.Exec.escript(
            name="Task1", script="print 'Post delete task runs after VM is deleted'"
        )


class HelloDeployment(Deployment):
    """Sample Deployment"""

    packages = [ref(HelloPackage)]
    substrate = ref(HelloSubstrate)


class HelloProfile(Profile):

    # Deployments under this profile
    deployments = [HelloDeployment]

    restore_configs = [AppProtection.RestoreConfig("r1")]
    snapshot_configs = [AppProtection.SnapshotConfig("s1")]
    environments = [Ref.Environment(name="env1")]


class DSLSnapshotRestore(Blueprint):
    """ Sample blueprint for Hello app using AHV VM"""

    credentials = [CentosCred]
    services = [HelloService]
    packages = [HelloPackage, CentosPackage]
    substrates = [HelloSubstrate]
    profiles = [HelloProfile]
