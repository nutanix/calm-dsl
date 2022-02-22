import json

from calm.dsl.builtins import SimpleDeployment, SimpleBlueprint
from calm.dsl.builtins import read_provider_spec, Ref, Metadata
from calm.dsl.builtins import read_local_file, basic_cred

DSL_CONFIG = json.loads(read_local_file(".tests/config.json"))

CENTOS_KEY = read_local_file(".tests/keys/centos")
CENTOS_PUBLIC_KEY = read_local_file(".tests/keys/centos_pub")

# project constants
PROJECT = DSL_CONFIG["PROJECTS"]["PROJECT1"]
PROJECT_NAME = PROJECT["NAME"]
ENV_NAME = PROJECT["ENVIRONMENTS"][0]["NAME"]
NTNX_LOCAL_ACCOUNT = DSL_CONFIG["ACCOUNTS"]["NTNX_LOCAL_AZ"]
SUBNET_UUID = NTNX_LOCAL_ACCOUNT["SUBNETS"][0]["UUID"]

Centos = basic_cred("centos", CENTOS_KEY, name="Centos", type="KEY", default=True)


class VmDeployment(SimpleDeployment):
    """Single VM service"""

    # VM Spec
    provider_spec = read_provider_spec("specs/ahv_provider_spec.yaml")
    provider_spec.spec["resources"]["nic_list"][0]["subnet_reference"][
        "uuid"
    ] = SUBNET_UUID


class SingleVmBlueprint(SimpleBlueprint):
    """Single VM blueprint"""

    credentials = [Centos]
    deployments = [VmDeployment]
    environments = [
        Ref.Environment(
            name=ENV_NAME,
        )
    ]


class BpMetadata(Metadata):

    project = Ref.Project(PROJECT_NAME)
