"""
Calm DSL Runbook Sample with default endpoint target
"""

from calm.dsl.runbooks import read_local_file
from calm.dsl.runbooks import runbook, runbook_json
from calm.dsl.runbooks import basic_cred, RunbookTask as Task
from calm.dsl.runbooks import CalmEndpoint as Endpoint

CRED_USERNAME = read_local_file(".tests/runbook_tests/username")
CRED_PASSWORD = read_local_file(".tests/runbook_tests/password")
VM_IP = read_local_file(".tests/runbook_tests/vm_ip")

Cred = basic_cred(CRED_USERNAME, CRED_PASSWORD, name="endpoint_cred")
endpoint = Endpoint.Linux.ip([VM_IP], cred=Cred)


@runbook
def DslDefaultEndpoint(endpoints=[endpoint]):
    """
    Runbook example with default target
    The default target for runbook is 'endpoints[0]'
    If no default target is required, 'default=False', can be given in runbook arguments
    Existing Endpoint can also be given as default target- 'default=ref(Endpoint.use_existing(<ep-name>))'
    """

    Task.Exec.ssh(script='echo "hello"')


def main():
    print(runbook_json(DslDefaultEndpoint))


if __name__ == "__main__":
    main()
