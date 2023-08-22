import json
import os

from calm.dsl.builtins import Account, AccountResources, AccountAuth
from calm.dsl.constants import ACCOUNT

CA_CERTIFICATE = "ca_certificate"
TOKEN = "token"
SERVER = "server"
PORT = "9440"
SYNC_INTERVAL_SECS = 3900


class test_k8s_vailla_account_123321(Account):
    """This is a test account"""

    type = ACCOUNT.TYPE.K8S_VANILLA
    sync_interval = SYNC_INTERVAL_SECS
    resources = AccountResources.K8s_Vanilla(
        auth=AccountAuth.K8s.service_account(
            ca_certificate=CA_CERTIFICATE,
            token=TOKEN,
        ),
        server=SERVER,
        port=PORT,
    )
