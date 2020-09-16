"""
Single Vm deployment interface for Calm DSL


"""
import sys
import json

from calm.dsl.builtins import ref, basic_cred
from calm.dsl.builtins import SingleVmBlueprint
from calm.dsl.builtins import read_local_file

from calm.dsl.builtins import AhvVmDisk, AhvVmNic, AhvVmGC
from calm.dsl.builtins import AhvVmResources, AhvVm, ahv_vm


# Credentials
CENTOS_KEY = read_local_file("keys/centos")
CENTOS_PUBLIC_KEY = read_local_file("keys/centos_pub")
Centos = basic_cred("centos", CENTOS_KEY, name="Centos", type="KEY", default=True)

DNS_SERVER = read_local_file(".tests/dns_server")

# Setting the recursion limit to max for
sys.setrecursionlimit(100000)


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

    serial_ports = {0: False, 1: False, 2: True, 3: True}


class SampleSingleVmBluerint(SingleVmBlueprint):
    """Simple blueprint Spec"""

    # VM Spec
    provider_spec = ahv_vm(resources=AhvVmResources)
