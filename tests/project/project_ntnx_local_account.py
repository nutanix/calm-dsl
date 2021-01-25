import json

from calm.dsl.builtins import Project
from calm.dsl.builtins import Provider, Ref, read_local_file


DSL_CONFIG = json.loads(read_local_file(".tests/config.json"))
NTNX_LOCAL_ACCOUNT = DSL_CONFIG["ACCOUNTS"]["NTNX_LOCAL_AZ"]

ACCOUNT_NAME = NTNX_LOCAL_ACCOUNT["NAME"]
SUBNET_NAME = NTNX_LOCAL_ACCOUNT["SUBNETS"][0]["NAME"]
CLUSTER_NAME = NTNX_LOCAL_ACCOUNT["SUBNETS"][0]["CLUSTER"]

VCPUS = 1
STORAGE = 2  # GiB
MEMORY = 1  # GiB


class DSL_PROJECT(Project):
    """Test project"""

    providers = [
        Provider.Ntnx(
            account=Ref.Account(ACCOUNT_NAME),
            subnets=[Ref.Subnet(name=SUBNET_NAME, cluster=CLUSTER_NAME)],
        )
    ]

    quotas = {"vcpus": VCPUS, "storage": STORAGE, "memory": MEMORY}
