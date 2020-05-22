import os

from calm.dsl.builtins import AhvVmDisk, AhvVmNic, AhvVmGC, AhvVmResources
from calm.dsl.builtins import read_local_file


# SSH Credentials
CENTOS_USER = "centos"
CENTOS_KEY = read_local_file(os.path.join("keys", "centos"))
CENTOS_PUBLIC_KEY = read_local_file(os.path.join("keys", "centos_pub"))


class MyAhvVm(AhvVmResources):
    """Example VM DSL"""

    memory = 4
    vCPUs = 2
    cores_per_vCPU = 1
    disks = [
        AhvVmDisk(
            image_name="Centos7",
            bootable=True,
            uuid="edfca6da-8d48-4cf7-aad9-3f3a63910c5b",
        ),
        AhvVmDisk.CdRom(
            image_name="SQLServer2014SP2", uuid="ae8b075e-c18a-4a80-9690-0cfac71ef771"
        ),
        AhvVmDisk.Disk.Pci.allocateOnStorageContainer(
            size=12, uuid="027d2bfe-1538-4e9a-a48a-2d39a2797707"
        ),
        AhvVmDisk.CdRom.Ide.emptyCdRom(uuid="3a3330cb-ceae-4248-aa42-b513cf81852d"),
        AhvVmDisk.CdRom.Ide.emptyCdRom(uuid="18ba76a4-b069-4595-a6bb-a16fc0adc5e4"),
    ]
    nics = [
        AhvVmNic.DirectNic.ingress(
            subnet="vlan.0",
            cluster="calmdev1",
            uuid="a181f7d8-1ab3-40f5-a2ac-4040c2682d3a",
        ),
        AhvVmNic.NormalNic.egress(
            subnet="vlan.0",
            cluster="calmdev1",
            uuid="3f464f27-7588-4d62-b98b-e7ecb1a0c1b9",
        ),
        AhvVmNic.DirectNic.tap(
            subnet="vlan.0", uuid="5fa71c6e-2bd2-4655-ac4e-9e92fb8a29bd"
        ),
    ]

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
