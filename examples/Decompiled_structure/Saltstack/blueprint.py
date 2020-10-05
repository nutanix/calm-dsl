# THIS FILE IS AUTOMATICALLY GENERATED.
# Disclaimer: Please test this file before using in production.
"""
Generated blueprint DSL (.py)
"""

import json  # no_qa
import os  # no_qa

from calm.dsl.builtins import *  # no_qa


# Secret Variables
BP_CRED_SSHUSER_KEY = read_local_file("BP_CRED_SSHUSER_KEY")

# Credentials
BP_CRED_SSHUSER = basic_cred(
    "centos",
    BP_CRED_SSHUSER_KEY,
    name="SSHUSER",
    type="KEY",
    default=True,
    editables={"username": True, "secret": True},
)


AHV_CENTOS_78 = vm_disk_package(
    name="AHV_CENTOS_78",
    description="",
    config={
        "image": {
            "name": "CENTOS-7-x86_64-2003",
            "type": "DISK_IMAGE",
            "source": "http://download.nutanix.com/Calm/CentOS-7-x86_64-2003.qcow2",
            "architecture": "X86_64",
        },
        "product": {},
        "checksum": {},
    },
)


class SaltStack_Master(Service):
    @action
    def __create__():
        """System action for creating an application"""

        CalmTask.Exec.ssh(
            name="SaltMaster Install and Configure",
            filename=os.path.join(
                "scripts",
                "Service_SaltStack_Master_Action___create___Task_SaltMasterInstallandConfigure.sh",
            ),
            cred=ref(BP_CRED_SSHUSER),
            target=ref(SaltStack_Master),
        )


class SaltStack_Minion(Service):
    @action
    def __create__():
        """System action for creating an application"""

        CalmTask.Exec.ssh(
            name="SaltMinion Configuration ",
            filename=os.path.join(
                "scripts",
                "Service_SaltStack_Minion_Action___create___Task_SaltMinionConfiguration.sh",
            ),
            target=ref(SaltStack_Minion),
        )

    @action
    def __start__():
        """System action for starting an application"""

        CalmTask.Exec.ssh(
            name="Configure Salt Minion",
            filename=os.path.join(
                "scripts",
                "Service_SaltStack_Minion_Action___start___Task_ConfigureSaltMinion.sh",
            ),
            cred=ref(BP_CRED_SSHUSER),
            target=ref(SaltStack_Minion),
        )


class SaltStackMastercalm_array_indexcalm_timeResources(AhvVmResources):

    memory = 4
    vCPUs = 2
    cores_per_vCPU = 1
    disks = [AhvVmDisk.Disk.Scsi.cloneFromVMDiskPackage(AHV_CENTOS_78, bootable=True)]
    nics = [AhvVmNic.NormalNic.ingress("vlan.0", cluster="Goten-1")]

    guest_customization = AhvVmGC.CloudInit(
        filename=os.path.join(
            "specs", "SaltStackMastercalm_array_indexcalm_time_cloud_init_data.yaml"
        )
    )


class SaltStackMastercalm_array_indexcalm_time(AhvVm):

    name = "SaltStack-Master-@@{calm_array_index}@@-@@{calm_time}@@"
    resources = SaltStackMastercalm_array_indexcalm_timeResources


class SaltStackMaster(Substrate):

    os_type = "Linux"
    provider_type = "AHV_VM"
    provider_spec = SaltStackMastercalm_array_indexcalm_time
    provider_spec_editables = read_spec(
        os.path.join("specs", "SaltStackMaster_create_spec_editables.yaml")
    )
    readiness_probe = readiness_probe(credential=ref(BP_CRED_SSHUSER), disabled=False)


class SaltStackMinioncalm_array_indexcalm_timeResources(AhvVmResources):

    memory = 4
    vCPUs = 2
    cores_per_vCPU = 1
    disks = [AhvVmDisk.Disk.Scsi.cloneFromVMDiskPackage(AHV_CENTOS_78, bootable=True)]
    nics = [AhvVmNic.NormalNic.ingress("vlan.0", cluster="Goten-1")]

    guest_customization = AhvVmGC.CloudInit(
        filename=os.path.join(
            "specs", "SaltStackMinioncalm_array_indexcalm_time_cloud_init_data.yaml"
        )
    )


class SaltStackMinioncalm_array_indexcalm_time(AhvVm):

    name = "SaltStack-Minion-@@{calm_array_index}@@-@@{calm_time}@@"
    resources = SaltStackMinioncalm_array_indexcalm_timeResources


class SaltStackMinion(Substrate):

    os_type = "Linux"
    provider_type = "AHV_VM"
    provider_spec = SaltStackMinioncalm_array_indexcalm_time
    provider_spec_editables = read_spec(
        os.path.join("specs", "SaltStackMinion_create_spec_editables.yaml")
    )
    readiness_probe = readiness_probe(credential=ref(BP_CRED_SSHUSER), disabled=False)

class ApproveKeys(Substrate):

    os_type = "Linux"
    provider_type = "EXISTING_VM"
    provider_spec = read_provider_spec(
        os.path.join("specs", "ApproveKeys_provider_spec.yaml")
    )
    provider_spec_editables = read_spec(
        os.path.join("specs", "ApproveKeys_create_spec_editables.yaml")
    )
    readiness_probe = readiness_probe(credential=ref(BP_CRED_SSHUSER), disabled=False)

class SaltStackMasterPackage(Package):

    services = [ref(SaltStack_Master)]


class Approver(Service):

    name = "Approver "

    dependencies = [ref(SaltStack_Minion)]

    @action
    def __start__():
        """System action for starting an application"""

        CalmTask.Exec.escript(
            name="Wait for Minion Keys",
            filename=os.path.join(
                "scripts", "Service_Approver_Action___start___Task_WaitforMinionKeys.py"
            ),
            target=ref(Approver),
        )
        CalmTask.Exec.ssh(
            name="ApproveKeys1",
            filename=os.path.join(
                "scripts", "Service_Approver_Action___start___Task_ApproveKeys1.sh"
            ),
            cred=ref(BP_CRED_SSHUSER),
            target=ref(Approver),
        )


class SaltStackMinionPackage(Package):

    services = [ref(SaltStack_Minion)]


class SaltStackMasterDeployment(Deployment):

    name = "SaltStackMasterDeployment"
    min_replicas = "1"
    max_replicas = "1"
    default_replicas = "1"

    packages = [ref(SaltStackMasterPackage)]
    substrate = ref(SaltStackMaster)


class Package3(Package):

    services = [ref(Approver)]


class SaltStackMinionDeployment(Deployment):

    name = "SaltStackMinionDeployment"
    min_replicas = "2"
    max_replicas = "5"
    default_replicas = "2"

    packages = [ref(SaltStackMinionPackage)]
    substrate = ref(SaltStackMinion)


class ApproveKeysDeployment(Deployment):

    min_replicas = "1"
    max_replicas = "1"
    default_replicas = "1"

    packages = [ref(Package3)]
    substrate = ref(ApproveKeys)


class Nutanix(Profile):

    deployments = [
        SaltStackMasterDeployment,
        SaltStackMinionDeployment,
        ApproveKeysDeployment,
    ]

    MASTER_HOSTNAME = CalmVariable.Simple(
        "saltstackmaster",
        label="",
        is_mandatory=False,
        is_hidden=False,
        runtime=True,
        description="",
    )

    MINION_HOSTNAME = CalmVariable.Simple(
        "saltstackminion",
        label="",
        is_mandatory=False,
        is_hidden=False,
        runtime=True,
        description="",
    )

    @action
    def ApplyDesiredState():
        """This action used to deploy git on all SaltStack Minions"""

        CalmTask.Exec.ssh(
            name="ApplyState",
            filename=os.path.join(
                "scripts", "Profile_Nutanix_Action_ApplyDesiredState_Task_ApplyState.sh"
            ),
            cred=ref(BP_CRED_SSHUSER),
            target=ref(SaltStack_Master),
        )


class Saltstack(Blueprint):
    """Accessibility:
* Command line"""

    services = [SaltStack_Master, SaltStack_Minion, Approver]
    packages = [SaltStackMasterPackage, SaltStackMinionPackage, Package3, AHV_CENTOS_78]
    substrates = [SaltStackMaster, SaltStackMinion, ApproveKeys]
    profiles = [Nutanix]
    credentials = [BP_CRED_SSHUSER]
