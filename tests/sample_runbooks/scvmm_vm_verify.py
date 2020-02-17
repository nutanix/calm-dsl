"""
Calm Runbook for scvmm vm verify
"""

from calm.dsl.builtins import read_local_file, basic_cred
from calm.dsl.builtins import runbook
from calm.dsl.builtins import CalmTask
from calm.dsl.builtins import CalmEndpoint, ref

CRED_USERNAME = read_local_file(".tests/runbook_tests/username")
CRED_PASSWORD = read_local_file(".tests/runbook_tests/password")
VM_IP = read_local_file(".tests/runbook_tests/vm_ip")

Cred = basic_cred(CRED_USERNAME, CRED_PASSWORD, name="SCVMM")
SCVMMEndpoint = CalmEndpoint.Windows.ip([VM_IP], cred=Cred)


@runbook
def DslScvmmVMCreate(endpoints=[SCVMMEndpoint], default_target=ref(SCVMMEndpoint)):
    "Verify vm in scvmm"
    CalmTask.Exec.escript(
        script="print 'Successfully connected to HyperV'"
    )


def main():
    print(DslScvmmVMCreate.runbook.json_dumps(pprint=True))


if __name__ == "__main__":
    main()
