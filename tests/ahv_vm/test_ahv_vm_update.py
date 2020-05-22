import os

from calm.dsl.builtins import AhvVmDisk, AhvVmNic, AhvVmGC, AhvVmResources
from calm.dsl.builtins import read_local_file


# SSH Credentials
CENTOS_USER = "centos"
CENTOS_KEY = read_local_file(os.path.join("keys", "centos"))
CENTOS_PUBLIC_KEY = read_local_file(os.path.join("keys", "centos_pub"))


class MyAhvVm(AhvVmResources):
    """Example VM DSL"""

    memory = 1
    vCPUs = 1
    cores_per_vCPU = 1
    disks = [
        AhvVmDisk(
            image_name="Centos7",
            bootable=True,
            uuid="635f4dd0-6693-4900-97f6-ab2a086f7f39",
        ),
        AhvVmDisk.CdRom(
            image_name="SQLServer2014SP2", uuid="4e128a84-4fe5-415f-9b9e-daa77263180a"
        ),
        AhvVmDisk.Disk.Pci.allocateOnStorageContainer(
            size=12, uuid="0df7ab31-16cb-4a01-9843-fd73fdee18bc"
        ),
        AhvVmDisk.CdRom.Ide.emptyCdRom(uuid="aa210234-00ec-4a6d-a6b3-c3813a7be399"),
        AhvVmDisk.CdRom.Ide.emptyCdRom(uuid="1f1f1a70-848e-43ef-939b-a7cbab3d8da9"),
    ]
    nics = [
        AhvVmNic.DirectNic.ingress(
            subnet="vlan.0",
            cluster="calmdev1",
            uuid="4518d3f8-1675-4946-8db9-fbe804cc5a66",
        ),
        AhvVmNic.NormalNic.egress(
            subnet="vlan.0",
            cluster="calmdev1",
            uuid="008f92ff-b57e-4905-b40f-a1d7feed7c7a",
        ),
        AhvVmNic.DirectNic.tap(
            subnet="vlan.0", uuid="3846f3c1-e1ff-4b98-9385-e7ea95eca90c"
        ),
    ]
    power_state = "OFF"
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


def test_json():
    print(MyAhvVm.json_dumps(pprint=True))


if __name__ == "__main__":
    test_json()
