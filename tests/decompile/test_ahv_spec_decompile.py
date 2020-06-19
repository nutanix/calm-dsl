from calm.dsl.builtins import AhvVmType, AhvVmResourcesType
from calm.dsl.builtins import read_spec

def test_decompile():

    spec = read_spec("ahv_spec.json")

    vm_cls = AhvVmType.dcompile(spec)



