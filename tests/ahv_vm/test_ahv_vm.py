from calm.dsl.builtins import AhvVmDisk, AhvVmNic, AhvVmGC, AhvVmGpu
from calm.dsl.builtins import basic_cred, ahv_vm_resources
from calm.dsl.builtins import vm_disk_package, read_local_file
from calm.dsl.builtins.models.metadata_payload import get_metadata_payload
from calm.dsl.config import get_context


AhvVm = ahv_vm_resources()

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
        AhvVmDisk(image_name="Centos7", bootable=True),
        AhvVmDisk.CdRom(image_name="SQLServer2014SP2"),
        AhvVmDisk.CdRom.Sata(image_name="SQLServer2014SP2"),
        AhvVmDisk.Disk.Scsi.cloneFromImageService(image_name="AHV_CENTOS_76"),
        AhvVmDisk.Disk.Pci.allocateOnStorageContainer(size=12),
        AhvVmDisk.CdRom.Sata.emptyCdRom(),
        AhvVmDisk.CdRom.Ide.emptyCdRom(),
        AhvVmDisk.Disk.Scsi.cloneFromVMDiskPackage(Era),
    ]
    nics = [
        AhvVmNic(subnet="vlan.0", cluster="calmdev1"),
        AhvVmNic.DirectNic.egress(subnet="vlan.0", cluster="calmdev1"),
        AhvVmNic.DirectNic.ingress(subnet="vlan.0", cluster="calmdev1"),
        AhvVmNic.DirectNic.tap(subnet="vlan.0"),
        AhvVmNic.NormalNic.egress(subnet="vlan.0", cluster="calmdev1"),
        AhvVmNic.NormalNic.ingress(subnet="vlan.0"),
        AhvVmNic.NormalNic.tap(subnet="vlan.0"),
        AhvVmNic.NetworkFunctionNic.tap(),
        AhvVmNic.NetworkFunctionNic(),
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

    # Ahv Helpers uses Metadata Context, It should the context(if any) defined in this file only
    get_metadata_payload(__file__)
    ContextObj = get_context()
    ContextObj.reset_configuration()

    print(MyAhvVm.json_dumps(pprint=True))


if __name__ == "__main__":
    test_json()
