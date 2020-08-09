"""
Calm VM Endpoint Example with Static Filter
"""

from calm.dsl.runbooks import read_local_file
from calm.dsl.runbooks import basic_cred
from calm.dsl.runbooks import CalmEndpoint as Endpoint
from calm.dsl.runbooks import CalmAccount as Account
from calm.dsl.runbooks import ENDPOINT_FILTER, ENDPOINT_PROVIDER

CRED_USERNAME = read_local_file(".tests/runbook_tests/username")
CRED_PASSWORD = read_local_file(".tests/runbook_tests/password")
AHV_LINUX_ID = read_local_file(".tests/runbook_tests/ahv_linux_id")
LinuxCred = basic_cred(CRED_USERNAME, CRED_PASSWORD, name="endpoint_cred")


AHVStaticVMEndpoint = Endpoint.Linux.vm(
    filter_type=ENDPOINT_FILTER.STATIC,
    values=[AHV_LINUX_ID],
    cred=LinuxCred,
    provider_type=ENDPOINT_PROVIDER.NUTANIX,
    account=Account.NutanixPC("NTNX_LOCAL_AZ"),
)


def main():
    print(AHVStaticVMEndpoint.json_dumps(pprint=True))


if __name__ == "__main__":
    main()
