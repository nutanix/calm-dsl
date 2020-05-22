import os

from calm.dsl.builtins import AhvVmDisk, AhvVmNic, AhvVmGC, AhvVmResources
from calm.dsl.builtins import read_local_file, read_env


# SSH Credentials
CENTOS_USER = "centos"
CENTOS_KEY = read_local_file(os.path.join("keys", "centos"))
CENTOS_PUBLIC_KEY = read_local_file(os.path.join("keys", "centos_pub"))

ENV = read_env()


class MyAhvVmDslTest(AhvVmResources):
    """Example VM DSL"""

    memory = 1
    vCPUs = 1
    cores_per_vCPU = 1
    disks = [
        AhvVmDisk(image_name="Centos7", bootable=True, uuid=ENV.get("DISK1_UUID"),),
        AhvVmDisk.CdRom(image_name="SQLServer2014SP2", uuid=ENV.get("DISK2_UUID"),),
        AhvVmDisk.Disk.Pci.allocateOnStorageContainer(
            size=12, uuid=ENV.get("DISK3_UUID"),
        ),
        AhvVmDisk.CdRom.Ide.emptyCdRom(uuid=ENV.get("DISK4_UUID"),),
        AhvVmDisk.CdRom.Ide.emptyCdRom(uuid=ENV.get("DISK5_UUID"),),
    ]
    nics = [
        AhvVmNic.DirectNic.ingress(
            subnet="vlan.0", cluster="calmdev1", uuid=ENV.get("NIC1_UUID"),
        ),
        AhvVmNic.NormalNic.egress(
            subnet="vlan.0", cluster="calmdev1", uuid=ENV.get("NIC2_UUID"),
        ),
        AhvVmNic.DirectNic.tap(subnet="vlan.0", uuid=ENV.get("NIC3_UUID"),),
    ]
    power_state = "ON"
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
