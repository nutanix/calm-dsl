# THIS FILE IS AUTOMATICALLY GENERATED.
"""
Sample Calm DSL for Hello blueprint

The top-level folder contains the following files:
HelloBlueprint/
├── .local
│   └── keys
│       ├── centos
│       └── centos_pub
├── blueprint.py
└── scripts
    ├── pkg_install_task.sh
    └── pkg_uninstall_task.sh

On launch, this blueprint does the following:
  1. Creates AHV VM (2 vCPUs, 4G Mem, 1 core)
  2. Installs CentOS 7 by downloading image from http://download.nutanix.com.
  3. Injects SSH public key in the VM using cloud init.
  4. Creates calm credential using the SSH private key to run tasks on the VM.

Order of execution for every deployment during blueprint launch:
  1. Substrate.__pre_create__() (Only http and escript tasks are allowed here)
  2. Substrate.__create__() (Generated from provider_spec)
  3. Package.__install__() (Scripts to install application go here)
  4. Service.__create__() (Scripts to configure and create the service go here)
  5. Service.__start__() (Scripts to start the service go here)

Useful commands (execute from top-level directory):
  1. calm compile bp --file HelloBlueprint/blueprint.py
  2. calm create bp --file HelloBlueprint/blueprint.py --name <blueprint_name>
  3. calm get bps --name <blueprint_name>
  4. calm describe bp <blueprint_name>
  5. calm launch bp <blueprint_name> --app_name <app_name> -i
  6. calm get apps --name <app_name>
  7. calm describe app <app_name>
  8. calm delete app <app_name>
  9. calm delete bp <blueprint_name>

"""

import os

from calm.dsl.builtins import Service, Package, Substrate
from calm.dsl.builtins import (
    Deployment,
    Profile,
    Blueprint,
)
from calm.dsl.builtins import CalmVariable as Variable
from calm.dsl.builtins import CalmVariable as Variable
from calm.dsl.builtins import CalmTask as Task
from calm.dsl.builtins import action, parallel, ref, basic_cred
from calm.dsl.builtins import read_local_file
from calm.dsl.builtins import vm_disk_package, AhvVmDisk, AhvVmNic
from calm.dsl.builtins import AhvVmGC, AhvVmResources, AhvVm
from calm.dsl.builtins import AppEdit, PatchField, AhvUpdateConfigAttrs


# SSH Credentials
CENTOS_USER = "centos"
CentosCred = basic_cred(
    CENTOS_USER,
    "PASSWORD",
    name="Centos",
    type="PASSWORD",
    default=True,
)


class HelloService(Service):
    """Sample Service"""

    # Service Variables
    ENV = Variable.WithOptions.Predefined.string(
        ["DEV", "PROD"], default="DEV", is_mandatory=True, runtime=True
    )

    # Custom service actions
    @action
    def custom_action_1():
        """Sample service action"""

        # Step 1
        Task.Exec.ssh(name="Task11", script='echo "Hello"')

        # Step 2
        Task.Exec.ssh(name="Task12", script='echo "Hello again"')

    @action
    def custom_action_2():

        # Step 1
        Task.Exec.ssh(name="Task21", script="date")

        # Step 2
        with parallel():  # All tasks within this context will be run in parallel
            Task.Exec.ssh(name="Task22a", script="date")
            Task.Exec.ssh(name="Task22b", script="date")

        # Step 3
        Task.Exec.ssh(name="Task23", script="date")


class HelloPackage(Package):
    """Sample Package"""

    # Services created by installing this Package
    services = [ref(HelloService)]

    # Package Variables
    sample_pkg_var = Variable.Simple("Sample package installation")


class HelloVmResources(AhvVmResources):

    memory = 1
    vCPUs = 1
    cores_per_vCPU = 1
    disks = [
        AhvVmDisk.Disk.Scsi.cloneFromImageService(image_name="hadoop", bootable=True),
        AhvVmDisk.Disk.Pci.allocateOnStorageContainer(10),
        AhvVmDisk.Disk.Pci.allocateOnStorageContainer(10),
    ]
    nics = [
        AhvVmNic.DirectNic.ingress(
            subnet="nested_vms", cluster="auto_cluster_prod_1a5e1b6769ad"
        ),
        AhvVmNic.DirectNic.ingress(
            subnet="nested_vms", cluster="auto_cluster_prod_1a5e1b6769ad"
        ),
    ]


class HelloVm(AhvVm):

    resources = HelloVmResources
    categories = {"AppFamily": "Demo", "AppType": "Default"}


class HelloSubstrate(Substrate):
    """AHV VM Substrate"""

    provider_type = "AHV_VM"
    provider_spec = HelloVm


class HelloDeployment(Deployment):
    """Sample Deployment"""

    packages = [ref(HelloPackage)]
    substrate = ref(HelloSubstrate)


class AhvUpdateAttrs(AhvUpdateConfigAttrs):
    """AHV VM update attrs"""

    memory = PatchField.Ahv.vcpu(
        value="2", operation="equal", max_val=0, min_val=0, editable=False
    )
    vcpu = PatchField.Ahv.vcpu(value="2", operation="equal", max_val=0, min_val=0)
    numsocket = PatchField.Ahv.vcpu(value="2", operation="equal", max_val=0, min_val=0)
    disk_delete = True
    categories_delete = True
    nic_delete = True
    categories_add = True
    nics = [
        PatchField.Ahv.Nics.delete(index=1, editable=True),
        PatchField.Ahv.Nics.add(
            AhvVmNic.DirectNic.ingress(
                subnet="nested_vms", cluster="auto_cluster_prod_1a5e1b6769ad"
            ),
            editable=False,
        ),
    ]
    disks = [
        PatchField.Ahv.Disks.delete(index=1),
        PatchField.Ahv.Disks.modify(
            index=2, editable=True, value="2", operation="equal", max_val=4, min_val=1
        ),
        PatchField.Ahv.Disks.add(
            AhvVmDisk.Disk.Pci.allocateOnStorageContainer(10),
            editable=False,
        ),
    ]
    categories = [
        PatchField.Ahv.Category.add({"TemplateType": "Vm"}),
        PatchField.Ahv.Category.delete({"AppFamily": "Demo", "AppType": "Default"}),
    ]


class HelloProfile(Profile):

    # Deployments under this profile
    deployments = [HelloDeployment]

    # Profile Variables
    var1 = Variable.Simple("sample_val1", runtime=True)
    var2 = Variable.Simple("sample_val2", runtime=True)
    var3 = Variable.Simple.int("2048", validate_regex=True, regex=r"^[\d]*$")
    patch_list = [
        AppEdit.UpdateConfig(
            "Update Hello", target=ref(HelloDeployment), patch_attrs=AhvUpdateAttrs
        )
    ]

    # Profile Actions
    @action
    def custom_profile_action_2():
        """Sample description for a profile action"""

        # Step 1: Run a task on a service in the profile
        Task.Exec.ssh(
            name="Task2",
            script='echo "Profile level action 2 using @@{var1}@@ and @@{var2}@@ and @@{var3}@@"',
            target=ref(HelloService),
        )

        # Step 2: Call service action as a task.
        # It will execute all tasks under the given action.
        HelloService.custom_action_1(name="Task7")

    # Profile Actions
    @action
    def custom_profile_action_1():
        """Sample description for a profile action"""

        # Step 1: Run a task on a service in the profile
        Task.Exec.ssh(
            name="Task1",
            script='echo "Profile level action using @@{var1}@@ and @@{var2}@@ and @@{var3}@@"',
            target=ref(HelloService),
        )

        # Step 2: Call service action as a task.
        # It will execute all tasks under the given action.
        HelloService.custom_action_1(name="Task6")


class Hello(Blueprint):
    """Sample blueprint for Hello app using AHV VM"""

    credentials = [CentosCred]
    services = [HelloService]
    packages = [HelloPackage]
    substrates = [HelloSubstrate]
    profiles = [HelloProfile]
