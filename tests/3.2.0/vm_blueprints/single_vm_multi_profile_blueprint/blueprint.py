"""
Single vm across multi-profiles interface.
NOTE: Multi-Vm Blueprint will be created as result.

"""
import os

from calm.dsl.builtins import ref, basic_cred, Ref
from calm.dsl.builtins import read_local_file, readiness_probe
from calm.dsl.builtins import CalmTask as Task
from calm.dsl.builtins import CalmVariable as Var
from calm.dsl.builtins import action

from calm.dsl.builtins import AhvVmDisk, AhvVmNic, AhvVmGC
from calm.dsl.builtins import AhvVmResources, ahv_vm
from calm.dsl.builtins import VmProfile, VmBlueprint


# Credentials
CENTOS_KEY = read_local_file("keys/centos")
CENTOS_PUBLIC_KEY = read_local_file("keys/centos_pub")
Centos = basic_cred("centos", CENTOS_KEY, name="Centos", type="KEY", default=True)

DNS_SERVER = read_local_file(".tests/dns_server")


class SmallAhvVmResources(AhvVmResources):
    """Vm configuration"""

    memory = 2
    vCPUs = 1
    cores_per_vCPU = 1
    disks = [
        AhvVmDisk.Disk.Scsi.cloneFromImageService("Centos7HadoopMaster", bootable=True)
    ]
    nics = [AhvVmNic("vlan1211")]

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


class AhvVmSmallProfile(VmProfile):
    """ Small Ahv Vm Profile"""

    # Profile variables
    nameserver = Var(DNS_SERVER, label="Local DNS resolver")

    # VM Spec for Substrate
    provider_spec = ahv_vm(resources=SmallAhvVmResources, name="SmallAhvVm")

    # Readiness probe for substrate (disabled is set to false, for enabling check login)
    readiness_probe = readiness_probe(credential=ref(Centos), disabled=False)

    environment = Ref.Environment(name="test_env_1", project="default")

    # Only actions under Packages, Substrates and Profiles are allowed
    @action
    def __install__():
        Task.Exec.ssh(
            name="Task1", filename=os.path.join("scripts", "mysql_install_script.sh")
        )

    @action
    def __pre_create__():
        Task.Exec.escript(name="Pre Create Task", script="print 'Hello!'")

    @action
    def test_profile_action():
        Task.Exec.ssh(name="Task9", script='echo "Hello"')


# NOTE: Inheriting `AhvVmSmallProfile` class to inherit disks and nics
class LargeAhvVmResources(SmallAhvVmResources):
    """ Vm Ahv Resources """

    memory = 4
    vCPUs = 2
    cores_per_vCPU = 2


# NOTE: Inheriting `AhvVmSmallProfile` class to inherit variables and actions
class AhvVmLargeProfile(AhvVmSmallProfile):
    """ Large Ahv Vm  Profile """

    provider_spec = ahv_vm(resources=LargeAhvVmResources, name="LargeAhvVm")


class SampleSingleVmBluerint(VmBlueprint):
    """Simple blueprint Spec"""

    # Blueprint credentials
    credentials = [Centos]

    # Blueprint profiles
    profiles = [AhvVmSmallProfile, AhvVmLargeProfile]
