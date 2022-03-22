"""
Calm DSL Decision Task Example

"""

from calm.dsl.runbooks import read_local_file
from calm.dsl.runbooks import runbook, runbook_json
from calm.dsl.runbooks import RunbookTask as Task
from calm.dsl.runbooks import CalmEndpoint as Endpoint, ref, basic_cred

CRED_USERNAME = read_local_file(".tests/runbook_tests/username")
CRED_PASSWORD = read_local_file(".tests/runbook_tests/password")
VM_IP = read_local_file(".tests/runbook_tests/vm_ip")

Cred = basic_cred(CRED_USERNAME, CRED_PASSWORD, name="endpoint_cred")
endpoint = Endpoint.Linux.ip([VM_IP], cred=Cred)


@runbook
def DslDecisionRunbook(endpoints=[endpoint]):
    """
    Runbook example with decision task
    Decision tasks can be defined in 2 ways
    1. with Task.Decision() as d:
        if d.ok:
            true_path
        else:
            false_path
    2. with Task.Decision() as d:
        if d.exit_code == 0:
            true_path
        if d.exit_code == 1:
            false_path
    """

    with Task.Decision.ssh(
        name="DecisionTask",
        script="cat hell",
        target=ref(Endpoint.use_existing("DslEndpoint")),
    ) as d:

        if d.ok:
            Task.Exec.escript(
                name="Task1", script="print 'Decision Task is Successful'"
            )

        else:
            Task.Exec.escript(name="Task2", script="print 'Decision Task Failed'")
