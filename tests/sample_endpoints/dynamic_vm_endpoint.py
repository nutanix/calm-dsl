"""
Calm VM Endpoint Example with Dynamic Filter
"""

from calm.dsl.runbooks import read_local_file
from calm.dsl.runbooks import basic_cred, Ref
from calm.dsl.runbooks import CalmEndpoint as Endpoint

CRED_USERNAME = read_local_file(".tests/runbook_tests/username")
CRED_PASSWORD = read_local_file(".tests/runbook_tests/password")
LinuxCred = basic_cred(CRED_USERNAME, CRED_PASSWORD, name="endpoint_cred")


AHVDynamicVMEndpoint = Endpoint.Linux.vm(
    filter="name==linux_vm.*;category==cat1:value1",
    cred=LinuxCred,
    account=Ref.Account("NTNX_LOCAL_AZ"),
)
