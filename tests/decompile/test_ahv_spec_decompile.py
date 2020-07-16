from calm.dsl.builtins import AhvVmType
from calm.dsl.builtins import read_spec
from calm.dsl.decompile.ahv_vm_disk import render_ahv_vm_disk
from calm.dsl.decompile.ahv_vm_nic import render_ahv_vm_nic
from calm.dsl.decompile.ahv_vm_gc import render_ahv_vm_gc
from calm.dsl.decompile.ahv_vm_gpu import render_ahv_vm_gpu
from calm.dsl.decompile.ahv_vm_resources import render_ahv_vm_resources
from calm.dsl.decompile.ahv_vm import render_ahv_vm


def test_decompile():

    spec = read_spec("ahv_spec.json")
    boot_config = spec["resources"].get("boot_config", {})
    vm_cls = AhvVmType.decompile(spec)
    print(render_ahv_vm(vm_cls, boot_config))

    vm_resources = vm_cls.resources
    print(render_ahv_vm_resources(vm_resources, boot_config=boot_config))

    # Get rendered disks
    for disk in vm_resources.disks:
        print(render_ahv_vm_disk(disk, boot_config))

    for nic in vm_resources.nics:
        print(render_ahv_vm_nic(nic))

    # TODO take care of generating file
    guest_customization_str = render_ahv_vm_gc(
        vm_resources.guest_customization, vm_name_prefix="vm_test"
    )
    print(guest_customization_str)

    for gpu in vm_resources.gpus:
        print(render_ahv_vm_gpu(gpu))
