from calm.dsl.builtins import Brownfield as BF
from calm.dsl.builtins import read_local_file

INSTANCE_NAME = read_local_file("brownfield_instance_name")


class AhvVmDeployment(BF.Deployment):

    # Note: If multiple instance with same name exists, send ip_address or instance_id too
    # Ex: instance = [BF.Vm.Ahv(name=<instance_name>, ip_address = [ip1, ip2], instance_id = 'instance_id')]
    instances = [
        BF.Vm.Ahv(INSTANCE_NAME)
    ]
