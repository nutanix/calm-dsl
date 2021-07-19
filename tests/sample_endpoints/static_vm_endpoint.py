"""
Calm VM Endpoint Example with Static Filter
"""

from calm.dsl.runbooks import read_local_file
from calm.dsl.runbooks import basic_cred, Ref
from calm.dsl.runbooks import CalmEndpoint as Endpoint

CRED_USERNAME = read_local_file(".tests/runbook_tests/username")
CRED_PASSWORD = read_local_file(".tests/runbook_tests/password")
AHV_LINUX_ID = read_local_file(".tests/runbook_tests/ahv_linux_id")
LinuxCred = basic_cred(CRED_USERNAME, CRED_PASSWORD, name="endpoint_cred")


AHVStaticVMEndpoint = Endpoint.Linux.vm(
    vms=[Ref.Vm(name="hitesh1")],
    cred=LinuxCred,
    account=Ref.Account("NTNX_LOCAL_AZ"),
)
