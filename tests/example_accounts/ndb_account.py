import json

from calm.dsl.builtins import Account, AccountResources
from calm.dsl.builtins import Ref

from calm.dsl.constants import ACCOUNT


class test_ndb_123321(Account):

    type = ACCOUNT.TYPE.NDB
    resources = AccountResources.NDBProvider(
        parent=Ref.Account("NTNX_LOCAL_AZ"),
        variable_dict={
            "server_ip": "ENDPOINT_VALUE",
            "username": "USERNAME_VALUE",
            "password": "PASSWORD_VALUE",
        },
    )
