from calm.dsl.builtins import AhvVmType, AhvVmResourcesType
from calm.dsl.builtins import read_spec
from calm.dsl.decompile.ahv_vm_disk import render_ahv_vm_disk
from calm.dsl.decompile.ahv_vm_nic import render_ahv_vm_nic


def test_decompile():

    spec = read_spec("ahv_spec.json")
    vm_cls = AhvVmType.decompile(spec)

    vm_resources = vm_cls.resources

    # Get rendered disks
    for disk in vm_resources.disks:
        print(render_ahv_vm_disk(disk))
    
    for nic in vm_resources.nics:
        print(render_ahv_vm_nic(nic))

    import pdb

    pdb.set_trace()
