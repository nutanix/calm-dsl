import json

from calm.dsl.builtins import Project
from calm.dsl.builtins import Provider, Ref, read_local_file

DSL_CONFIG = json.loads(read_local_file(".tests/config.json"))
ACCOUNTS = DSL_CONFIG["ACCOUNTS"]["NUTANIX_PC"]

NTNX_ACCOUNT = [
    account for account in ACCOUNTS if account["NAME"].startswith("multipc_account")
][0]
NTNX_ACCOUNT_NAME = NTNX_ACCOUNT["NAME"]
NTNX_ACCOUNT_UUID = NTNX_ACCOUNT["UUID"]

NTNX_SUBNET = NTNX_ACCOUNT["SUBNETS"][0]["NAME"]
NTNX_SUBNET_CLUSTER = NTNX_ACCOUNT["SUBNETS"][0]["CLUSTER"]

USER = DSL_CONFIG["USERS"][0]
USER_NAME = USER["NAME"]

GROUP = DSL_CONFIG["USER_GROUPS"][0]
GROUP_NAME = GROUP["NAME"]


class TestDslProject(Project):
    """Sample DSL Project"""

    providers = [
        Provider.Ntnx(
            account=Ref.Account(NTNX_ACCOUNT_NAME),
            subnets=[Ref.Subnet(name=NTNX_SUBNET, cluster=NTNX_SUBNET_CLUSTER)],
            clusters=[
                Ref.Cluster(name=NTNX_SUBNET_CLUSTER, account_name=NTNX_ACCOUNT_NAME)
            ],
        )
    ]

    users = [Ref.User(name=USER_NAME)]

    groups = [Ref.Group(name=GROUP_NAME)]

    quotas = {"vcpus": 1, "storage": 2, "memory": 1}
