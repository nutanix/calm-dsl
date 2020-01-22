"""
Calm Runbook Sample for running http tasks
"""
from calm.dsl.builtins import read_local_file
from calm.dsl.builtins import runbook, RunbookService
from calm.dsl.builtins import CalmTask, basic_cred
from calm.dsl.builtins import CalmEndpoint, ref

linux_ip = read_local_file(".tests/runbook_tests/vm_ip")
windows_ip = read_local_file(".tests/runbook_tests/vm_ip")
CRED_USERNAME = read_local_file(".tests/runbook_tests/username")
CRED_PASSWORD = read_local_file(".tests/runbook_tests/password")
Cred = basic_cred(CRED_USERNAME, CRED_PASSWORD, name="endpoint_cred")
linux_endpoint = CalmEndpoint.Linux.ip([linux_ip, linux_ip], cred=Cred)


class EscriptTask(RunbookService):
    "Runbook Service example"

    @runbook
    def main_runbook():
        CalmTask.Exec.escript(name="ExecTask", script='''print "Task is Successful"''')

    endpoints = []
    credentials = []


class SetVariableOnEscript(RunbookService):
    "Runbook Service example"

    @runbook
    def main_runbook():
        CalmTask.SetVariable.escript(name="SetVariableTask", script='''print "task_state=Successful"''', variables=["task_state"])
        CalmTask.Exec.escript(name="ExecTask", script='''print "Task is @@{task_state}@@"''')

    endpoints = []
    credentials = []


class EscriptOnEndpoint(RunbookService):
    "Runbook Service example"

    @runbook
    def main_runbook():
        CalmTask.Exec.escript(name="ExecTask",
                              script='''print "Task is Successful"''',
                              target=ref(linux_endpoint))

    credentials = []
    endpoints = [linux_endpoint]
