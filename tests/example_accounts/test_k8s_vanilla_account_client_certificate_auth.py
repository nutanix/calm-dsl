import json
import os

from calm.dsl.builtins import Account, AccountResources, AccountAuth
from calm.dsl.constants import ACCOUNT

CERTIFICATE = "certificate"
KEY = "key"
SERVER = "server"
PORT = "9440"
SYNC_INTERVAL_SECS = 3900


class test_k8s_vailla_account_123321(Account):
    """This is a test account"""

    type = ACCOUNT.TYPE.K8S_VANILLA
    sync_interval = SYNC_INTERVAL_SECS
    resources = AccountResources.K8s_Vanilla(
        auth=AccountAuth.K8s.client_certificate(
            client_certificate=CERTIFICATE,
            client_key=KEY,
        ),
        server=SERVER,
        port=PORT,
    )
