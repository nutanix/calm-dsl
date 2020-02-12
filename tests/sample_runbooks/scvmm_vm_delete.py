"""
Calm Runbook for scvmm vm delete
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
def DslScvmmVMDelete(endpoints=[SCVMMEndpoint], default_target=ref(SCVMMEndpoint)):
    "Delete vm in scvmm"
    VM_NAME = CalmVariable.Simple.string("", runtime=True)  # noqa
    CalmTask.Exec.powershell(
        filename="/Users/sarat.kumar/Scripts/hackathon2020/scvmm_vm_delete.ps1"
    )


def main():
    print(DslScvmmVMDelete.runbook.json_dumps(pprint=True))


if __name__ == "__main__":
    main()
