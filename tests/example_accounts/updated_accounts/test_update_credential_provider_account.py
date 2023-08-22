import json
import os

from calm.dsl.runbooks import runbook, ref
from calm.dsl.runbooks import RunbookTask as Task
from calm.dsl.runbooks import CalmEndpoint as Endpoint
from calm.dsl.builtins import (
    Account,
    CalmVariable,
    action,
    CredAccountResources,
    AccountResources,
)

from calm.dsl.constants import ACCOUNT

SYNC_INTERVAL_SECS = 1900

VAULT_URI = "VAULT_URI_UPDATED"
VAULT_TOKEN = "VAULT_TOKEN_UPDATED"

VAR_NAME = "VAR1_UPDATED"
VAR_VALUE = "VAR1_VALUE_UPDATED"

VAR_NAME_2 = "VAR2_UPDATED"
VAR_VALUE_2 = "VAR2_VALUE_UPDATED"

SEC_VAR_NAME = "SEC_VAR1_UPDATED"
SEC_VAR_VALUE = "SEC_VAR1_VALUE_UPDATED"

SEC_VAR_NAME_2 = "SEC_VAR2_UPDATED"
SEC_VAR_VALUE_2 = "SEC_VAR2_VALUE_UPDATED"


class HashiCorpResources(CredAccountResources):

    variables = [
        CalmVariable.Simple.string(name=VAR_NAME, value=VAR_VALUE),
        CalmVariable.Simple.Secret.string(name=SEC_VAR_NAME, value=SEC_VAR_VALUE),
    ]

    cred_attrs = [
        CalmVariable.Simple.string(name=VAR_NAME_2, value=VAR_VALUE_2),
        CalmVariable.Simple.Secret.string(name=SEC_VAR_NAME_2, value=SEC_VAR_VALUE_2),
    ]

    @action
    def DslSetVariableRunbook():
        "Runbook example with Set Variable Tasks"

        Task.Exec.escript(name="Task1", script="print '@@{var1}@@ @@{var2}@@'")
        Task.Exec.escript(name="Task2", script="print '@@{var1}@@ @@{var2}@@'")


class HashiCorpVault_Cred_Provider(Account):
    """This is a test credential provider"""

    type = ACCOUNT.TYPE.CREDENTIAL_PROVIDER
    resources = AccountResources.CredentialProvider(
        vault_uri="VAULT_URI_VALUE_UPDATED",
        vault_token="VAULT_TOKEN_VALUE_UPDATED",
        resource_config=HashiCorpResources,
    )
