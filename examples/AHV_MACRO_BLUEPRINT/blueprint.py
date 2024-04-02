"""
This blueprint uses macro in nic and disk
"""

import os  # no_qa

from calm.dsl.builtins import *  # no_qa
from examples.AHV_MACRO_BLUEPRINT.sample_runbook import DslSetVariableRunbook


# Secret Variables
CRED_USERNAME = read_local_file("cred_username")
CRED_PASSWORD = read_local_file("cred_password")


class Service1(Service):
    """Sample Service"""

    # disk image uuid to be used in disk image
    Custom_disk_uuid = CalmVariable.Simple.string(
        "e7b96d85-f41b-40a1-bd23-310b7de14eb1"
    )


class Package1(Package):
    """Sample package"""

    services = [ref(Service1)]


class VmResources(AhvVmResources):

    memory = 2
    vCPUs = 2
    cores_per_vCPU = 2
    disks = [
        AhvVmDisk.Disk.Scsi.cloneFromImageService(
            "@@{Service1.Custom_disk_uuid}@@", bootable=True
        )
    ]
    nics = [AhvVmNic.NormalNic.ingress("@@{custom_nic.uuid}@@")]


class VMSubstrate(Substrate):
    """Sample Substrate"""

    provider_spec = ahv_vm(
        name="vm-@@{calm_array_index}@@-@@{calm_time}@@", resources=VmResources
    )

    @action
    def __pre_create__():
        CalmTask.SetVariable.escript.py3(
            name="Pre_create task1",
            filename=os.path.join("scripts", "pre_create_script.py"),
            target=ref(VMSubstrate),
            variables=["custom_nic"],
        )


class MacroBlueprintDeployment(Deployment):
    """Sample Deployment"""

    packages = [ref(Package1)]
    substrate = ref(VMSubstrate)


class MacroBlueprintProfile(Profile):
    """Sample Profile"""

    foo1 = CalmVariable.Simple("bar1", runtime=True)
    foo2 = CalmVariable.Simple("bar2", runtime=True)
    deployments = [MacroBlueprintDeployment]

    # For profile, actions task_target_mapping is compulsory
    http_task_action = get_runbook_action(
        DslSetVariableRunbook,
        targets={
            "Task1": ref(Service1),
            "Task2": ref(Service1),
            "Task3": ref(Service1),
        }
    )

    @action
    def test_profile_action():
        """Sample description for a profile action"""
        CalmTask.Exec.ssh(name="Task5", script='echo "Hello"', target=ref(Service1))


class MacroBlueprint(Blueprint):
    """Blueprint using macro in disk and nics"""

    services = [Service1]
    packages = [Package1]
    substrates = [VMSubstrate]
    profiles = [MacroBlueprintProfile]
    credentials = [basic_cred(CRED_USERNAME, CRED_PASSWORD, default=True)]
