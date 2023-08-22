import json
import os

from calm.dsl.builtins import Account, AccountResources
from calm.dsl.constants import ACCOUNT


TENANT_ID = "tenant_id"
CLIENT_ID = "client_id"
CLIENT_KEY = "client_key"
SYNC_INTERVAL_SECS = 3900


class test_azure_account_123321(Account):
    """This is a test account"""

    type = ACCOUNT.TYPE.AZURE
    sync_interval = 3900
    resources = AccountResources.Azure(
        tenant_id=TENANT_ID,
        client_id=CLIENT_ID,
        client_key=CLIENT_KEY,
        cloud="PublicCloud",
    )
