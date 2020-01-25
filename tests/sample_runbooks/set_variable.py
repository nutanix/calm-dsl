"""
Calm Runbook Sample for set variable task
"""

from calm.dsl.builtins import read_local_file
from calm.dsl.builtins import runbook
from calm.dsl.builtins import CalmTask
from calm.dsl.builtins import CalmEndpoint, ref, basic_cred

CRED_USERNAME = read_local_file(".tests/runbook_tests/username")
CRED_PASSWORD = read_local_file(".tests/runbook_tests/password")
VM_IP = read_local_file(".tests/runbook_tests/vm_ip")

Cred = basic_cred(CRED_USERNAME, CRED_PASSWORD, name="endpoint_cred")
endpoint = CalmEndpoint.Linux.ip([VM_IP], cred=Cred)


@runbook
def DslSetVariableTask(endpoints=[endpoint]):
    "Runbook Service example"
    CalmTask.SetVariable.escript(
        script="print 'var1=test'",
        variables=["var1"],
    )
    CalmTask.SetVariable.ssh(
        filename="scripts/sample_script.sh",
        variables=["var2"],
        target=ref(endpoint),
    )
    CalmTask.Exec.escript(
        script="print '@@{var1}@@ @@{var2}@@'"
    )


def main():
    print(DslSetVariableTask.runbook.json_dumps(pprint=True))


if __name__ == "__main__":
    main()
