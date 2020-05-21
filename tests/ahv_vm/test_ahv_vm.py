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
        AhvVmDisk(image_name="Centos7", bootable=True),
    ]
    nics = [
        AhvVmNic.DirectNic.ingress(
            subnet="vlan.0", cluster="calmdev1"
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
