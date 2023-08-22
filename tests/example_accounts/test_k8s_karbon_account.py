import json
import os

from calm.dsl.builtins import Account, AccountResources, read_local_file
from calm.dsl.constants import ACCOUNT

DSL_CONFIG = json.loads(read_local_file(".tests/config.json"))

CLUSTER_NAME = DSL_CONFIG["ACCOUNTS"]["NTNX_LOCAL_AZ"]["SUBNETS"][1]["CLUSTER"]
SYNC_INTERVAL_SECS = 3900


class test_k8s_karbon_account_123321(Account):
    """This is a test account"""

    type = ACCOUNT.TYPE.K8S_KARBON
    sync_interval = SYNC_INTERVAL_SECS
    resources = AccountResources.K8s_Karbon(cluster=CLUSTER_NAME)
