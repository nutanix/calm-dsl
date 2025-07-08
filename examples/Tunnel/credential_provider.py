import json
import os

from calm.dsl.runbooks import runbook, ref
from calm.dsl.runbooks import RunbookTask as Task
from calm.dsl.runbooks import CalmEndpoint as Endpoint
from calm.dsl.runbooks import read_local_file
from calm.dsl.builtins import (
    Account,
    CalmVariable,
    action,
    CredAccountResources,
    AccountResources,
    Ref,
)

from calm.dsl.constants import ACCOUNT

DSL_CONFIG = json.loads(read_local_file(".tests/config.json"))
TUNNEL_1 = DSL_CONFIG["TUNNELS"]["TUNNEL_1"]["NAME"]
TUNNEL_2 = DSL_CONFIG["TUNNELS"]["TUNNEL_2"]["NAME"]


class Test_DSL_HashiCorpResources(CredAccountResources):

    variables = [
        CalmVariable.Simple.string(name="VAR1", value="VAR1_VALUE"),
        CalmVariable.Simple.Secret.string(name="SEC_VAR1", value="SEC_VAR1_VALUE"),
    ]

    cred_attrs = [
        CalmVariable.Simple.string(name="VAR2", value="VAR2_VALUE"),
        CalmVariable.Simple.Secret.string(name="SEC_VAR2", value="SEC_VAR2_VALUE"),
    ]

    @action
    def DslSetVariableRunbook():
        "Runbook example with Set Variable Tasks"

        Task.Exec.escript(name="Task1", script="print '@@{var1}@@ @@{var2}@@'", tunnel=Ref.Tunnel.Account(name=TUNNEL_1))
        Task.Exec.escript(name="Task2", script="print '@@{var1}@@ @@{var2}@@'", tunnel=Ref.Tunnel.Account(name=TUNNEL_2))


class Test_DSL_HashiCorpVault_Cred_Provider(Account):
    """This is a test credential provider"""

    type = ACCOUNT.TYPE.CREDENTIAL_PROVIDER
    tunnel = Ref.Tunnel.Account(name=TUNNEL_1)
    resources = AccountResources.CredentialProvider(
        vault_uri="VAULT_URI_VALUE",
        vault_token="VAULT_TOKEN_VALUE",
        resource_config=Test_DSL_HashiCorpResources,
    )
