"""
Calm Runbook for scvmm vm create
"""

from calm.dsl.builtins import read_local_file, basic_cred
from calm.dsl.builtins import runbook
from calm.dsl.builtins import CalmTask, CalmVariable
from calm.dsl.builtins import CalmEndpoint, ref

CRED_USERNAME = read_local_file(".tests/runbook_tests/username")
CRED_PASSWORD = read_local_file(".tests/runbook_tests/password")
VM_IP = read_local_file(".tests/runbook_tests/vm_ip")

Cred = basic_cred(CRED_USERNAME, CRED_PASSWORD, name="SCVMM")
SCVMMEndpoint = CalmEndpoint.Windows.ip([VM_IP], cred=Cred)


@runbook
def DslScvmmVMCreate(endpoints=[SCVMMEndpoint], default_target=ref(SCVMMEndpoint)):
    "Create vm in scvmm"
    VM_NAME = CalmVariable.Simple.string("", runtime=True)  # noqa
    CalmTask.SetVariable.powershell(
        filename="/Users/sarat.kumar/Scripts/hackathon2020/scvmm_vm_create.ps1",
        variables=["IpAddress"]
    )
    CalmTask.Exec.escript(
        script="print '@@{IpAddress}@@'"
    )


def main():
    print(DslScvmmVMCreate.runbook.json_dumps(pprint=True))


if __name__ == "__main__":
    main()
