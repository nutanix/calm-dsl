from calm.dsl.builtins import Brownfield as BF


class AhvVmDeployment(BF.Deployment):

    instances = [BF.Vm.Ahv("Vm3")]
