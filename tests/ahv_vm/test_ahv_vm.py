import json

from calm.dsl.builtins import AhvVmDisk, AhvVmNic, AhvVmGC, AhvVmGpu
from calm.dsl.builtins import basic_cred, ahv_vm_resources
from calm.dsl.builtins import vm_disk_package, read_local_file
from calm.dsl.config import get_context


AhvVm = ahv_vm_resources()

DSL_CONFIG = json.loads(read_local_file(".tests/config.json"))
CENTOS_HM = DSL_CONFIG["AHV"]["IMAGES"]["DISK"]["CENTOS_HADOOP_MASTER"]
CENTOS_CI = DSL_CONFIG["AHV"]["IMAGES"]["DISK"]["CENTOS_7_CLOUD_INIT"]
SQL_SERVER_IMAGE = DSL_CONFIG["AHV"]["IMAGES"]["CD_ROM"]["SQL_SERVER_2014_x64"]
NETWORK1 = DSL_CONFIG["AHV"]["NETWORK"]["VLAN1211"]

# projects
PROJECT = DSL_CONFIG["PROJECTS"]["PROJECT1"]
PROJECT_NAME = PROJECT["NAME"]

CENTOS_USERNAME = read_local_file(".tests/centos_username")
CENTOS_PASSWORD = read_local_file(".tests/centos_password")
CENTOS_SSH_USERNAME = read_local_file(".tests/centos_ssh_username")
CENTOS_SSH_KEY = read_local_file(".tests/centos_ssh_key")


DefaultCred = basic_cred(CENTOS_USERNAME, CENTOS_PASSWORD, name="CENTOS", default=True)
DefaultKeyCred = basic_cred(
    CENTOS_SSH_USERNAME, CENTOS_SSH_KEY, name="CENTOS_KEY", type="key"
)
Era = vm_disk_package(name="era", config_file="specs/era_image_config.yaml")


class MyAhvVm(AhvVm):

    memory = 2
    vCPUs = 2
    cores_per_vCPU = 1
    disks = [
        AhvVmDisk(image_name=CENTOS_HM, bootable=True),
        AhvVmDisk.CdRom(image_name=SQL_SERVER_IMAGE),
        AhvVmDisk.CdRom.Sata(image_name=SQL_SERVER_IMAGE),
        AhvVmDisk.Disk.Scsi.cloneFromImageService(image_name=CENTOS_CI),
        AhvVmDisk.Disk.Pci.allocateOnStorageContainer(size=12),
        AhvVmDisk.CdRom.Sata.emptyCdRom(),
        AhvVmDisk.CdRom.Ide.emptyCdRom(),
        AhvVmDisk.Disk.Scsi.cloneFromVMDiskPackage(Era),
    ]
    nics = [
        AhvVmNic(subnet=NETWORK1),
        AhvVmNic.DirectNic.egress(subnet=NETWORK1),
        AhvVmNic.DirectNic.ingress(subnet=NETWORK1),
        AhvVmNic.DirectNic.tap(subnet=NETWORK1),
        AhvVmNic.NormalNic.egress(subnet=NETWORK1),
        AhvVmNic.NormalNic.ingress(subnet=NETWORK1),
        AhvVmNic.NormalNic.tap(subnet=NETWORK1),
        AhvVmNic.NetworkFunctionNic.tap(),
        AhvVmNic.NetworkFunctionNic(),
        AhvVmNic("@@{substrate_variable}@@"),
    ]
    boot_type = "UEFI"

    """
    guest_customization = AhvVmGC.Sysprep.PreparedScript.withDomain(
        filename="guest_cus.xml",
        domain="1.1.1.1",
        dns_ip="1.1.1.1",
        credential=ref(DefaultCred),
    )
    """
    guest_customization = AhvVmGC.CloudInit(filename="specs/guest_cust_cloud_init.yaml")

    serial_ports = {0: False, 1: False, 2: True, 3: True}

    gpus = [
        AhvVmGpu.Amd.passThroughCompute(device_id=111),
        AhvVmGpu.Nvidia.virtual(device_id=212),
    ]


def test_json():

    ContextObj = get_context()

    ContextObj.update_project_context(project_name=PROJECT_NAME)
    print(MyAhvVm.json_dumps(pprint=True))
    ContextObj.reset_configuration()


def test_macro_in_nic():
    """Tests macro in vm nics"""

    import json

    ContextObj = get_context()
    ContextObj.update_project_context(project_name=PROJECT_NAME)
    vm_data = json.loads(MyAhvVm.json_dumps())
    assert (
        vm_data["nic_list"][9]["subnet_reference"]["uuid"] == "@@{substrate_variable}@@"
    )
    ContextObj.reset_configuration()
