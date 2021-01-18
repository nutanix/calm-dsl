"""
Single AHV VM Blueprint Example

"""

from calm.dsl.builtins import SimpleDeployment, SimpleBlueprint
from calm.dsl.builtins import read_provider_spec, Ref


class VmDeployment(SimpleDeployment):
    """Single VM service"""

    # VM Spec
    provider_spec = read_provider_spec("specs/ahv_provider_spec.yaml")


class SingleVmBlueprint(SimpleBlueprint):
    """Single VM blueprint"""

    deployments = [VmDeployment]
    environments = [Ref.Environment(name="env1", project="dsl_project")]


def test_single_vm_bp():

    import json

    bp_dict = SingleVmBlueprint.make_single_vm_bp_dict()
    generated_json = json.dumps(bp_dict, indent=4)
    print(generated_json)


if __name__ == "__main__":
    test_single_vm_bp()
