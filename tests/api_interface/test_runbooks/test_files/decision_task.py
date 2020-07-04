"""
Calm DSL Decision Task Example

"""

from calm.dsl.runbooks import runbook
from calm.dsl.runbooks import RunbookTask as Task
from calm.dsl.runbooks import CalmEndpoint as Endpoint
from calm.dsl.runbooks import read_local_file, basic_cred

linux_ip = read_local_file(".tests/runbook_tests/vm_ip")
windows_ip = read_local_file(".tests/runbook_tests/windows_vm_ip")
CRED_USERNAME = read_local_file(".tests/runbook_tests/username")
CRED_WINDOWS_USERNAME = read_local_file(".tests/runbook_tests/windows_username")
CRED_PASSWORD = read_local_file(".tests/runbook_tests/password")

LinuxCred = basic_cred(CRED_USERNAME, CRED_PASSWORD, name="linux_cred")
WindowsCred = basic_cred(CRED_WINDOWS_USERNAME, CRED_PASSWORD, name="windows_cred")

linux_endpoint = Endpoint.Linux.ip([linux_ip], cred=LinuxCred)
windows_endpoint = Endpoint.Windows.ip([windows_ip], cred=WindowsCred)


@runbook
def DecisionTask(endpoints=[linux_endpoint, windows_endpoint], default=False):
    "Runbook Service example"
    with Task.Decision.ssh(script="exit 0", target=endpoints[0]) as d:

        if d.ok:
            Task.Exec.ssh(name="SUCCESS1", script="echo 'SUCCESS'", target=endpoints[0])

        else:
            Task.Exec.ssh(name="FAILURE1", script="echo 'FAILURE'", target=endpoints[0])

    with Task.Decision.ssh(script="exit 1", target=endpoints[0]) as d:

        if d.ok:
            Task.Exec.ssh(name="SUCCESS2", script="echo 'SUCCESS'", target=endpoints[0])

        else:
            Task.Exec.ssh(name="FAILURE2", script="echo 'FAILURE'", target=endpoints[0])

    with Task.Decision.powershell(script="exit 0", target=endpoints[1]) as d:

        if d.ok:
            Task.Exec.powershell(
                name="SUCCESS3", script="echo 'SUCCESS'", target=endpoints[1]
            )

        else:
            Task.Exec.powershell(
                name="FAILURE3", script="echo 'FAILURE'", target=endpoints[1]
            )

    with Task.Decision.powershell(script="exit 1", target=endpoints[1]) as d:

        if d.ok:
            Task.Exec.powershell(
                name="SUCCESS4", script="echo 'SUCCESS'", target=endpoints[1]
            )

        else:
            Task.Exec.powershell(
                name="FAILURE4", script="echo 'FAILURE'", target=endpoints[1]
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
