import json

from calm.dsl.builtins import Account, AccountResources
from calm.dsl.constants import ACCOUNT
from calm.dsl.config import get_context

context = get_context()
SERVER_CONFIG = context.get_server_config()

USERNAME = "username"
PASSWORD = "password"
SERVER = SERVER_CONFIG["pc_ip"]
PORT = SERVER_CONFIG["pc_port"]
SYNC_INTERVAL_SECS = 3900


class test_ahv_account_123321(Account):
    """This is a test account"""

    type = ACCOUNT.TYPE.AHV
    sync_interval = SYNC_INTERVAL_SECS
    resources = AccountResources.Ntnx(
        username=USERNAME, password=PASSWORD, server=SERVER, port=PORT
    )
