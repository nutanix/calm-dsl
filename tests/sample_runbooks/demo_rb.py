"""
Calm DSL Demo 1

"""

from calm.dsl.builtins import read_local_file, basic_cred
from calm.dsl.builtins import runbook
from calm.dsl.builtins import CalmTask, CalmVariable
from calm.dsl.builtins import CalmEndpoint, ref
from calm.dsl.builtins import TaskInput

CRED_USERNAME = read_local_file(".tests/runbook_tests/username")
CRED_PASSWORD = read_local_file(".tests/runbook_tests/password")
VM_IP = read_local_file(".tests/runbook_tests/vm_ip")

Cred = basic_cred(CRED_USERNAME, CRED_PASSWORD, name="endpoint_cred")
DslLinuxEndpoint = CalmEndpoint.Linux.ip([VM_IP], cred=Cred)


@runbook
def DslDemoRunbook(endpoints=[DslLinuxEndpoint], default_target=ref(DslLinuxEndpoint)):
    "Runbook Service example"
    size_limit = CalmVariable.Simple.int("102400", runtime=True)  # noqa
    CalmTask.Input(name="InputTask", inputs=[TaskInput("log_path")])
    with CalmTask.Decision.ssh(name="DecisionTask", script="cd @@{log_path}@@"):
        def success():
            CalmTask.SetVariable.ssh(
                name="StoreLogsSizeBeforeCleanup",
                script='''echo "size_before_cleanup="$(du -d 0 @@{log_path}@@ | awk  "{print $1}")''',
                variables=["size_before_cleanup"]
            )
            CalmTask.Exec.ssh(name="Cleanup", filename="scripts/cleanup_logs.sh")
            CalmTask.SetVariable.ssh(
                name="StoreLogsSizeAfterCleanup",
                script='''echo "size_after_cleanup="$(du -d 0 @@{log_path}@@ | awk  "{print $1}")''',
                variables=["size_after_cleanup"]
            )
            CalmTask.Exec.escript(
                name="FinalOutput",
                script="print 'logs size changed from @@{size_before_cleanup}@@ => @@{size_after_cleanup}@@'",
                target=ref(DslLinuxEndpoint)
            )

        def failure():
            CalmTask.Exec.escript(script='''print "Given Logs Directory doesn't exists"''')


def main():
    print(DslDemoRunbook.runbook.json_dumps(pprint=True))


if __name__ == "__main__":
    main()
