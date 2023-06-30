import json
import os

from calm.dsl.builtins import Account, AccountResources
from calm.dsl.constants import ACCOUNT

ACCESS_KEY_ID = "access_key_id_updated"
SECRET_ACCESS_KEY = "secret_access_key_updated"
SYNC_INTERVAL_SECS = 3900


class test_aws_updated_account_123321(Account):
    """This is a test account"""

    type = ACCOUNT.TYPE.AWS
    sync_interval = SYNC_INTERVAL_SECS
    resources = AccountResources.Aws(
        access_key_id=ACCESS_KEY_ID,
        secret_access_key=SECRET_ACCESS_KEY,
        regions=[{"name": "us-east-1"}],
    )
