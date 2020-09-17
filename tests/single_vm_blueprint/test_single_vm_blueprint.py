"""
Single Vm deployment interface for Calm DSL

"""

from calm.dsl.builtins import ref, basic_cred
from calm.dsl.builtins import SingleVmBlueprint
from calm.dsl.builtins import read_local_file, readiness_probe
from calm.dsl.builtins import CalmTask as Task
from calm.dsl.builtins import CalmVariable as Var
from calm.dsl.builtins import action, parallel

from calm.dsl.builtins import AhvVmDisk, AhvVmNic, AhvVmGC
from calm.dsl.builtins import AhvVmResources, AhvVm, ahv_vm
from calm.dsl.builtins import Ref, Metadata


# Credentials
CENTOS_KEY = read_local_file("keys/centos")
CENTOS_PUBLIC_KEY = read_local_file("keys/centos_pub")
Centos = basic_cred("centos", CENTOS_KEY, name="Centos", type="KEY", default=True)

DNS_SERVER = read_local_file(".tests/dns_server")


class SingleVmAhvResources(AhvVmResources):
    """Vm configuration"""

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


class SampleSingleVmBluerint(SingleVmBlueprint):
    """Simple blueprint Spec"""

    # Blueprint credentials
    credentials = [Centos]

    # VM Spec for Substrate
    provider_spec = ahv_vm(resources=SingleVmAhvResources)

    # Readiness probe for substrate
    readiness_probe = readiness_probe(credential=ref(Centos), disabled=False)

    # Profile variables
    nameserver = Var(DNS_SERVER, label="Local DNS resolver")

    # Only actions under Packages, Substrates and Profiles are allowed
    @action
    def __install__():
        Task.Exec.ssh(name="Task1", filename="scripts/mysql_install_script.sh")

    @action
    def __pre_create__():
        Task.Exec.escript(name="Pre Create Task", script="print 'Hello!'")

    @action
    def test_profile_action():
        Task.Exec.ssh(name="Task9", script='echo "Hello"')


class BpMetadata(Metadata):

    project = Ref.Project("default")
