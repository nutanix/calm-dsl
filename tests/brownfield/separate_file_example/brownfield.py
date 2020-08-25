from calm.dsl.builtins import Brownfield as BF
from calm.dsl.builtins import read_local_file

VM_IP = read_local_file("vm_ip")


class AhvVmDeployment(BF.Deployment):

    instances = [BF.Vm.Ahv(ip_address=[VM_IP])]
