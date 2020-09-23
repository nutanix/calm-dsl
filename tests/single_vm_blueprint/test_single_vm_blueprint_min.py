"""
Single Vm deployment min interface for Calm DSL

"""

from calm.dsl.builtins import basic_cred
from calm.dsl.builtins import SingleVmBlueprint
from calm.dsl.builtins import read_local_file

from calm.dsl.builtins import AhvVmDisk, AhvVmNic, AhvVmGC
from calm.dsl.builtins import AhvVmResources, ahv_vm


# Credentials
CENTOS_KEY = read_local_file("keys/centos")
CENTOS_PUBLIC_KEY = read_local_file("keys/centos_pub")
Centos = basic_cred("centos", CENTOS_KEY, name="Centos", type="KEY", default=True)


class MyAhvVmResources(AhvVmResources):

    memory = 4
    vCPUs = 2
    cores_per_vCPU = 1
    disks = [AhvVmDisk.Disk.Scsi.cloneFromImageService("Centos7", bootable=True)]
    nics = [AhvVmNic("vlan.0")]

    guest_customization = AhvVmGC.CloudInit(
        config={
            "users": [
                {
                    "name": "centos",
                    "ssh-authorized-keys": [CENTOS_PUBLIC_KEY],
                    "sudo": ["ALL=(ALL) NOPASSWD:ALL"],
                }
            ]
        }
    )


class SingleVmMinInterfaceBluepeint(SingleVmBlueprint):
    """Simple blueprint Spec"""

    # Credentials
    credentials = [Centos]

    # VM Spec
    provider_spec = ahv_vm(resources=MyAhvVmResources)
