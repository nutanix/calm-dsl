"""
Calm Endpoint Sample of type Windows
"""

from calm.dsl.builtins import read_local_file
from calm.dsl.builtins import basic_cred
from calm.dsl.builtins import CalmEndpoint

CRED_USERNAME = read_local_file(".tests/runbook_tests/username")
CRED_PASSWORD = read_local_file(".tests/runbook_tests/password")
VM_IP = read_local_file(".tests/runbook_tests/vm_ip")

Cred = basic_cred(CRED_USERNAME, CRED_PASSWORD, name="endpoint_cred")
DslWindowsEndpoint = CalmEndpoint.Windows.ip([VM_IP], connection_protocol="HTTPS", cred=Cred)


def main():
    print(DslWindowsEndpoint.json_dumps(pprint=True))


if __name__ == "__main__":
    main()
