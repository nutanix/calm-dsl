from calm.dsl.builtins import AhvVmDisk, AhvVmNic, AhvVmGC
from calm.dsl.builtins import ref, basic_cred, AhvVmResources, AhvVm
from calm.dsl.builtins import vm_disk_package, read_spec

from calm.dsl.builtins import Service, Package, Substrate
from calm.dsl.builtins import Deployment, Profile, Blueprint
from calm.dsl.builtins import CalmVariable, CalmTask, action
from calm.dsl.builtins import read_local_file


CENTOS_PASSWORD = read_local_file("password")
CENTOS_KEY = read_local_file("private_key")

DefaultCred = basic_cred("centos", CENTOS_PASSWORD, name="CENTOS")
CentosKeyCred = basic_cred(
    "centos", CENTOS_KEY, name="CENTOS_KEY", type="KEY", default=True
)
Era_Disk = vm_disk_package(
    name="era_disk", config=read_spec("image_configs/era_disk.yaml")
)
Virtio_CdRom = vm_disk_package(
    name="virtio_cdrom", config_file="image_configs/virtio_cdrom.yaml"
)


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


class MyAhvVmResources(AhvVmResources):

    memory = 4
    vCPUs = 2
    cores_per_vCPU = 1
    disks = [
        AhvVmDisk("Centos7"),
        AhvVmDisk.CdRom("SQLServer2014SP2-FullSlipstream-x64"),
        AhvVmDisk.CdRom.Sata("SQLServer2014SP2-FullSlipstream-x64"),
        AhvVmDisk.CdRom.Ide("SQLServer2014SP2-FullSlipstream-x64"),
        AhvVmDisk.Disk.Scsi.cloneFromImageService("AHV_CENTOS_76", bootable=True),
        AhvVmDisk.Disk.Pci.allocateOnStorageContainer(12),
        AhvVmDisk.CdRom.Sata.emptyCdRom(),
        AhvVmDisk.CdRom.Ide.emptyCdRom(),
        AhvVmDisk.Disk.Scsi.cloneFromVMDiskPackage(Era_Disk),
        AhvVmDisk.CdRom.Sata.cloneFromVMDiskPackage(Virtio_CdRom),
    ]
    nics = [AhvVmNic("vlan.0"), AhvVmNic.DirectNic.egress("vlan.0")]

    guest_customization = AhvVmGC.CloudInit(filename="scripts/guest_cus.yaml")

    serial_ports = {0: False, 1: False, 2: True, 3: True}


class MyAhvVm(AhvVm):

    resources = MyAhvVmResources
    categories = {"AppFamily": "Backup", "AppType": "Default"}


class AHVVMforMySQL(Substrate):
    """AHV VM config given by reading a spec file"""

    provider_spec = MyAhvVm


class MySQLDeployment(Deployment):
    """Sample deployment pulling in service and substrate references"""

    packages = [ref(MySQLPackage)]
    substrate = ref(AHVVMforMySQL)


class DefaultProfile(Profile):
    """Sample application profile with variables"""

    nameserver = CalmVariable.Simple("10.40.64.15", label="Local DNS resolver")
    foo1 = CalmVariable.Simple("bar1", runtime=True)
    foo2 = CalmVariable.Simple("bar2", runtime=True)

    deployments = [MySQLDeployment]

    @action
    def test_profile_action():
        """Sample description for a profile action"""
        CalmTask.Exec.ssh(name="Task5", script='echo "Hello"', target=ref(MySQLService))


class AhvHelperDemoBp(Blueprint):
    """Sample Bp that used ahv_vm_helpers"""

    credentials = [DefaultCred, CentosKeyCred]
    services = [MySQLService]
    packages = [MySQLPackage, Era_Disk, Virtio_CdRom]
    substrates = [AHVVMforMySQL]
    profiles = [DefaultProfile]


def test_json():
    print(AhvHelperDemoBp.json_dumps(pprint=True))


if __name__ == "__main__":
    test_json()
