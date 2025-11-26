import json

from calm.dsl.builtins import Account, AccountResources, Ref
from calm.dsl.constants import ACCOUNT
from calm.dsl.config import get_context
from calm.dsl.runbooks import read_local_file

context = get_context()
SERVER_CONFIG = context.get_server_config()

USERNAME = "username"
PASSWORD = "password"
SERVER = SERVER_CONFIG["pc_ip"]
PORT = SERVER_CONFIG["pc_port"]
SYNC_INTERVAL_SECS = 3900

DSL_CONFIG = json.loads(read_local_file(".tests/config.json"))
TUNNEL_1 = DSL_CONFIG["TUNNELS"]["TUNNEL_1"]["NAME"]

class test_ahv_tunnel_account(Account):
    """This is a test account"""

    type = ACCOUNT.TYPE.AHV
    sync_interval = SYNC_INTERVAL_SECS
    tunnel = Ref.Tunnel.Account(name=TUNNEL_1)
    resources = AccountResources.Ntnx(
        username=USERNAME, password=PASSWORD, server=SERVER, port=PORT
    )