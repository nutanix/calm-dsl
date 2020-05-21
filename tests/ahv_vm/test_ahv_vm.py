from calm.dsl.builtins import AhvVmDisk, AhvVmNic, AhvVmGC, AhvVmGpu, AhvVmResources


class MyAhvVm(AhvVmResources):
    """Example VM DSL"""

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

    serial_ports = {0: False, 1: False, 2: True, 3: True}

    gpus = [
        AhvVmGpu.Amd.passThroughCompute(device_id=111),
        AhvVmGpu.Nvidia.virtual(device_id=212),
    ]


def test_json():
    print(MyAhvVm.json_dumps(pprint=True))


if __name__ == "__main__":
    test_json()
