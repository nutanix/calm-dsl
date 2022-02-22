"""
Single AHV VM Blueprint Example

"""

import json

from calm.dsl.builtins import SimpleDeployment, SimpleBlueprint
from calm.dsl.builtins import read_provider_spec, read_local_file

DSL_CONFIG = json.loads(read_local_file(".tests/config.json"))
NTNX_LOCAL_ACCOUNT = DSL_CONFIG["ACCOUNTS"]["NTNX_LOCAL_AZ"]
SUBNET_UUID = NTNX_LOCAL_ACCOUNT["SUBNETS"][0]["UUID"]


class VmDeployment(SimpleDeployment):
    """Single VM service"""

    # VM Spec
    provider_spec = read_provider_spec("specs/ahv_provider_spec.yaml")
    provider_spec.spec["resources"]["nic_list"][0]["subnet_reference"][
        "uuid"
    ] = SUBNET_UUID


class SingleVmBlueprint(SimpleBlueprint):
    """Single VM blueprint"""

    deployments = [VmDeployment]


def test_single_vm_bp():

    import json

    bp_dict = SingleVmBlueprint.make_single_vm_bp_dict()
    generated_json = json.dumps(bp_dict, indent=4)
    print(generated_json)


if __name__ == "__main__":
    test_single_vm_bp()
