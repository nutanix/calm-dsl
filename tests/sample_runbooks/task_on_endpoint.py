"""
Calm Runbook Sample for task running on an endpoint
"""

from calm.dsl.runbooks import read_local_file
from calm.dsl.runbooks import runbook
from calm.dsl.runbooks import basic_cred, RunbookTask as Task
from calm.dsl.runbooks import CalmEndpoint as Endpoint

CRED_USERNAME = read_local_file(".tests/runbook_tests/username")
CRED_PASSWORD = read_local_file(".tests/runbook_tests/password")
VM_IP = read_local_file(".tests/runbook_tests/vm_ip")

Cred = basic_cred(CRED_USERNAME, CRED_PASSWORD, name="endpoint_cred")
endpoint = Endpoint.Linux.ip([VM_IP], cred=Cred)

script = """
         echo "Welcome to task 1"
         hostname
         ip r s
         date
 """


@runbook
def DslTaskOnEndpoint(endpoints=[endpoint]):
    "Runbook Service example"
    Task.Exec.ssh(name="Task1", script=script)


def main():
    print(DslTaskOnEndpoint.runbook.json_dumps(pprint=True))


if __name__ == "__main__":
    main()
