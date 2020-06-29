"""
Calm DSL Decision Task Example

"""

from calm.dsl.builtins import runbook
from calm.dsl.builtins import CalmTask as Task
from calm.dsl.builtins import CalmEndpoint, ref
from calm.dsl.builtins import read_local_file, basic_cred

linux_ip = read_local_file(".tests/runbook_tests/vm_ip")
windows_ip = read_local_file(".tests/runbook_tests/windows_vm_ip")
CRED_USERNAME = read_local_file(".tests/runbook_tests/username")
CRED_WINDOWS_USERNAME = read_local_file(".tests/runbook_tests/windows_username")
CRED_PASSWORD = read_local_file(".tests/runbook_tests/password")

LinuxCred = basic_cred(CRED_USERNAME, CRED_PASSWORD, name="linux_cred")
WindowsCred = basic_cred(CRED_WINDOWS_USERNAME, CRED_PASSWORD, name="windows_cred")

linux_endpoint = CalmEndpoint.Linux.ip([linux_ip], cred=LinuxCred)
windows_endpoint = CalmEndpoint.Windows.ip([windows_ip], cred=WindowsCred)


@runbook
def DecisionTask(endpoints=[linux_endpoint, windows_endpoint]):
    "Runbook Service example"
    with Task.Decision.ssh(script="exit 0", target=ref(linux_endpoint)) as d:

        if d.ok:
            Task.Exec.ssh(
                name="SUCCESS1", script="echo 'SUCCESS'", target=ref(linux_endpoint)
            )

        else:
            Task.Exec.ssh(
                name="FAILURE1", script="echo 'FAILURE'", target=ref(linux_endpoint)
            )

    with Task.Decision.ssh(script="exit 1", target=ref(linux_endpoint)) as d:

        if d.ok:
            Task.Exec.ssh(
                name="SUCCESS2", script="echo 'SUCCESS'", target=ref(linux_endpoint)
            )

        else:
            Task.Exec.ssh(
                name="FAILURE2", script="echo 'FAILURE'", target=ref(linux_endpoint)
            )

    with Task.Decision.powershell(script="exit 0", target=ref(windows_endpoint)) as d:

        if d.ok:
            Task.Exec.powershell(
                name="SUCCESS3", script="echo 'SUCCESS'", target=ref(windows_endpoint)
            )

        else:
            Task.Exec.powershell(
                name="FAILURE3", script="echo 'FAILURE'", target=ref(windows_endpoint)
            )

    with Task.Decision.powershell(script="exit 1", target=ref(windows_endpoint)) as d:

        if d.ok:
            Task.Exec.powershell(
                name="SUCCESS4", script="echo 'SUCCESS'", target=ref(windows_endpoint)
            )

        else:
            Task.Exec.powershell(
                name="FAILURE4", script="echo 'FAILURE'", target=ref(windows_endpoint)
            )

    with Task.Decision.escript(script="exit(0)") as d:

        if d.ok:
            Task.Exec.escript(name="SUCCESS5", script="print 'SUCCESS'")

        else:
            Task.Exec.escript(name="FAILURE5", script="print 'FAILURE'")

    with Task.Decision.escript(script="exit(1)") as d:

        if d.ok:
            Task.Exec.escript(name="SUCCESS6", script="print 'SUCCESS'")

        else:
            Task.Exec.escript(name="FAILURE6", script="print 'FAILURE'")
