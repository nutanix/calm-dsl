import json

from calm.dsl.builtins import SimpleDeployment, SimpleBlueprint
from calm.dsl.builtins import read_provider_spec, Ref, Metadata
from calm.dsl.builtins import read_local_file, basic_cred

DSL_CONFIG = json.loads(read_local_file(".tests/config.json"))

CENTOS_KEY = read_local_file("keys/centos")
CENTOS_PUBLIC_KEY = read_local_file("keys/centos_pub")

# project constants
PROJECT = DSL_CONFIG["PROJECTS"]["PROJECT1"]
PROJECT_NAME = PROJECT["NAME"]
ENV_NAME = PROJECT["ENVIRONMENTS"][0]["NAME"]

Centos = basic_cred("centos", CENTOS_KEY, name="Centos", type="KEY", default=True)


class VmDeployment(SimpleDeployment):
    """Single VM service"""

    # VM Spec
    provider_spec = read_provider_spec("specs/ahv_provider_spec.yaml")


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
