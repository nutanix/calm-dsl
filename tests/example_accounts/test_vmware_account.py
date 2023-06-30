import json
import os

from calm.dsl.builtins import Account, AccountResources
from calm.dsl.constants import ACCOUNT

USERNAME = "username"
PASSWORD = "password"
SERVER = "10.44.44.13"
PORT = "9440"
SYNC_INTERVAL_SECS = 3900


class test_vmware_account_123321(Account):
    """This is a test account"""

    type = ACCOUNT.TYPE.VMWARE
    sync_interval = SYNC_INTERVAL_SECS
    resources = AccountResources.Vmware(
        username=USERNAME,
        password=PASSWORD,
        server=SERVER,
        port=PORT,
        price_items={"vcpu": 0.02, "memory": 0.01, "storage": 0.0003},
    )
