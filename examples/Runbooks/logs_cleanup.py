"""
Calm DSL Demo 1

"""

from calm.dsl.runbooks import read_local_file, basic_cred
from calm.dsl.runbooks import runbook, runbook_json
from calm.dsl.runbooks import RunbookTask as Task, RunbookVariable as Variable
from calm.dsl.runbooks import CalmEndpoint as Endpoint

CRED_USERNAME = read_local_file(".tests/runbook_tests/username")
CRED_PASSWORD = read_local_file(".tests/runbook_tests/password")
VM_IP = read_local_file(".tests/runbook_tests/vm_ip")

Cred = basic_cred(CRED_USERNAME, CRED_PASSWORD, name="endpoint_cred")
DslLinuxEndpoint = Endpoint.Linux.ip([VM_IP], cred=Cred)


@runbook
def DslLogsCleanupRunbook(endpoints=[DslLinuxEndpoint]):

    "Example runbook for cleaning up logs on a machine"
    size_limit = Variable.Simple.int("102400", runtime=True)  # noqa
    log_path = Variable.Simple("/logs", runtime=True)  # noqa
    with Task.Decision.ssh(name="DecisionTask", script="cd @@{log_path}@@") as d:

        if d.ok:
            Task.SetVariable.ssh(
                name="StoreLogsSizeBeforeCleanup",
                script="""echo "size_before_cleanup="$(du -d 0 @@{log_path}@@ | awk  "{print $1}")""",
                variables=["size_before_cleanup"],
            )
            Task.Exec.ssh(name="Cleanup", filename="scripts/cleanup_logs.sh")
            Task.SetVariable.ssh(
                name="StoreLogsSizeAfterCleanup",
                script="""echo "size_after_cleanup="$(du -d 0 @@{log_path}@@ | awk  "{print $1}")""",
                variables=["size_after_cleanup"],
            )
            Task.Exec.escript(
                name="FinalOutput",
                script="print 'logs size changed from @@{size_before_cleanup}@@ => @@{size_after_cleanup}@@'",
                target=endpoints[0],
            )

        else:
            Task.Exec.escript(script='''print "Given Logs Directory doesn't exists"''')


def main():
    print(runbook_json(DslLogsCleanupRunbook))


if __name__ == "__main__":
    main()
