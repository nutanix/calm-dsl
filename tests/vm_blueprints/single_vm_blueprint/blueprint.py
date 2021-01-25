"""
Single Vm across single profile
NOTE: Single-Vm Blueprint will be created as result

"""
import os
import json

from calm.dsl.builtins import ref, basic_cred
from calm.dsl.builtins import read_local_file, readiness_probe
from calm.dsl.builtins import CalmTask as Task
from calm.dsl.builtins import CalmVariable as Var
from calm.dsl.builtins import action

from calm.dsl.builtins import AhvVmDisk, AhvVmNic, AhvVmGC
from calm.dsl.builtins import AhvVmResources, ahv_vm
from calm.dsl.builtins import VmProfile, VmBlueprint
from calm.dsl.builtins import Metadata, Ref


# Credentials
CENTOS_KEY = read_local_file("keys/centos")
CENTOS_PUBLIC_KEY = read_local_file("keys/centos_pub")
Centos = basic_cred("centos", CENTOS_KEY, name="Centos", type="KEY", default=True)

DNS_SERVER = read_local_file(".tests/dns_server")

# projects
DSL_CONFIG = json.loads(read_local_file(".tests/config.json"))
CENTOS_7_CLOUD_INIT = DSL_CONFIG["AHV"]["IMAGES"]["DISK"]["CENTOS_7_CLOUD_INIT"]
NETWORK1 = DSL_CONFIG["AHV"]["NETWORK"]["VLAN1211"]

PROJECT = DSL_CONFIG["PROJECTS"]["PROJECT1"]
PROJECT_NAME = PROJECT["NAME"]


class SingleVmAhvResources(AhvVmResources):
    """Vm configuration"""

    memory = 4
    vCPUs = 2
    cores_per_vCPU = 1
    disks = [
        AhvVmDisk.Disk.Scsi.cloneFromImageService(CENTOS_7_CLOUD_INIT, bootable=True)
    ]
    nics = [AhvVmNic(NETWORK1)]

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

    # Readiness probe for substrate (disabled is set to false, for enabling check login)
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


class SampleSingleVmBluerint(VmBlueprint):
    """Simple blueprint Spec"""

    # Blueprint credentials
    credentials = [Centos]

    # Blueprint profiles
    profiles = [Profile1]


class SingleVmBpMetadata(Metadata):

    project = Ref.Project(PROJECT_NAME)
    categories = {"TemplateType": "Vm"}
