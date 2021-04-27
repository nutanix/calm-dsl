"""
Calm Runbook Sample for set variable task
"""

from calm.dsl.runbooks import read_local_file
from calm.dsl.runbooks import runbook, runbook_json
from calm.dsl.runbooks import RunbookTask as Task
from calm.dsl.runbooks import CalmEndpoint as Endpoint, basic_cred

CRED_USERNAME = read_local_file(".tests/runbook_tests/username")
CRED_PASSWORD = read_local_file(".tests/runbook_tests/password")
VM_IP = read_local_file(".tests/runbook_tests/vm_ip")

Cred = basic_cred(CRED_USERNAME, CRED_PASSWORD, name="endpoint_cred")
endpoint = Endpoint.Linux.ip([VM_IP], cred=Cred)


@runbook
def DslSetVariableTask(endpoints=[endpoint], default=False):
    "Runbook example with Set Variable Tasks"

    Task.SetVariable.escript(script="print 'var1=test'", variables=["var1"])
    Task.SetVariable.ssh(
        filename="scripts/sample_script.sh", variables=["var2"], target=endpoints[0]
    )
    Task.Exec.escript(script="print '@@{var1}@@ @@{var2}@@'")


def main():
    print(runbook_json(DslSetVariableTask))


if __name__ == "__main__":
    main()
