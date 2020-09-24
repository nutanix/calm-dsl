"""
Single Vm deployment interface for Calm DSL

"""
import os

from calm.dsl.builtins import ref, basic_cred
from calm.dsl.builtins import SingleVmBlueprint
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


class Profile1(VmProfile):

    # Profile variables
    nameserver = Var(DNS_SERVER, label="Local DNS resolver")

    # VM Spec for Substrate
    provider_spec = ahv_vm(resources=SingleVmAhvResources, name="MyAhvVm")

    # Readiness probe for substrate
    readiness_probe = readiness_probe(credential=ref(Centos), disabled=False)

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


class AhvVmProfile(Profile1):

    provider_type = "VMWARE_VM"
    # VM Spec for Substrate
    provider_spec = ahv_vm(resources=SingleVmAhvResources, name="MyAhvVm")


class SampleSingleVmBluerint(VmBlueprint):
    """Simple blueprint Spec"""

    # Blueprint credentials
    credentials = [Centos]

    profiles = [Profile1, AhvVmProfile]


template_type = "App"


"""def test_json():

    import sys

    from calm.dsl.config import get_context

    # Setting the recursion limit to max for
    sys.setrecursionlimit(100000)

    # Resetting context
    ContextObj = get_context()
    ContextObj.reset_configuration()

    dir_path = os.path.dirname(os.path.realpath(__file__))
    file_path = os.path.join(dir_path, "test_single_vm_bp_output.json")

    generated_json = SampleSingleVmBluerint.make_bp_obj().json_dumps(pprint=True)
    known_json = open(file_path).read()

    assert generated_json == known_json
"""

if __name__ == "__main__":

    print(SampleSingleVmBluerint.json_dumps(pprint=True))
