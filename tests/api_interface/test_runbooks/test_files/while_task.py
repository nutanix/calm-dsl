"""
Calm DSL While Task Example

"""
import json

from calm.dsl.runbooks import runbook
from calm.dsl.runbooks import RunbookTask as Task, Status
from calm.dsl.runbooks import CalmEndpoint as Endpoint
from calm.dsl.runbooks import read_local_file, basic_cred

linux_ip = read_local_file(".tests/runbook_tests/vm_ip")
windows_ip = read_local_file(".tests/runbook_tests/windows_vm_ip")
CRED_USERNAME = read_local_file(".tests/runbook_tests/username")
CRED_WINDOWS_USERNAME = read_local_file(".tests/runbook_tests/windows_username")
CRED_PASSWORD = read_local_file(".tests/runbook_tests/password")
URL = read_local_file(".tests/runbook_tests/url")
AUTH_USERNAME = read_local_file(".tests/runbook_tests/auth_username")
AUTH_PASSWORD = read_local_file(".tests/runbook_tests/auth_password")

LinuxCred = basic_cred(CRED_USERNAME, CRED_PASSWORD, name="linux_cred")
WindowsCred = basic_cred(CRED_WINDOWS_USERNAME, CRED_PASSWORD, name="windows_cred")

linux_endpoint = Endpoint.Linux.ip([linux_ip], cred=LinuxCred)
windows_endpoint = Endpoint.Windows.ip([windows_ip], cred=WindowsCred)
http_endpoint = Endpoint.HTTP(
    URL, verify=False, auth=Endpoint.Auth(AUTH_USERNAME, AUTH_PASSWORD)
)


@runbook
def WhileTask(endpoints=[linux_endpoint, windows_endpoint, http_endpoint]):
    "Runbook Service example"
    with Task.Loop(10, exit_condition=Status.SUCCESS):
        with Task.Decision.ssh(name="Task1", script="exit 0", target=endpoints[0]) as d:

            if d.ok:
                Task.Exec.ssh(
                    name="SUCCESS1", script="echo 'SUCCESS'", target=endpoints[0]
                )

            else:
                Task.Exec.ssh(
                    name="FAILURE1", script="echo 'FAILURE'", target=endpoints[0]
                )

        with Task.Decision.ssh(name="Task2", script="exit 1", target=endpoints[0]) as d:

            if d.ok:
                Task.Exec.ssh(
                    name="SUCCESS2", script="echo 'SUCCESS'", target=endpoints[0]
                )

            else:
                Task.Exec.ssh(
                    name="FAILURE2", script="echo 'FAILURE'", target=endpoints[0]
                )

        Task.Delay(15, name="Task3")
        Task.Delay(15, name="Task4")
        Task.HTTP.post(
            name="Task5",
            relative_url="/list",
            body=json.dumps({}),
            headers={"Content-Type": "application/json"},
            content_type="application/json",
            status_mapping={200: True},
            target=endpoints[2],
        )
        Task.HTTP.post(
            name="Task6",
            relative_url="/list",
            body=json.dumps({}),
            headers={"Content-Type": "application/json"},
            content_type="application/json",
            status_mapping={200: True},
            target=endpoints[2],
        )
        with Task.Loop(
            10, name="Task7", loop_variable="iteration1", exit_condition=Status.SUCCESS
        ):
            Task.Exec.escript(script="print 'test'")
        with Task.Loop(
            10, name="Task8", loop_variable="iteration2", exit_condition=Status.SUCCESS
        ):
            Task.Exec.escript(script="print 'test'")
        Task.Exec.escript(script="print 'test'", name="Task9")
        Task.Exec.escript(script="print 'test'", name="Task10")
        Task.Exec.ssh(script="echo 'test'", name="Task11", target=endpoints[0])
        Task.Exec.ssh(script="echo 'test'", name="Task12", target=endpoints[0])
        Task.Exec.powershell(script="echo 'test'", name="Task13", target=endpoints[1])
        Task.Exec.powershell(script="echo 'test'", name="Task14", target=endpoints[1])


@runbook
def WhileTaskLoopVariable(endpoints=[http_endpoint]):
    "Runbook Service example"
    with Task.Loop(10, name="Task1", loop_variable="iteration"):
        Task.SetVariable.escript(
            name="SetVariableTask",
            script='''print "iteration=random"''',
            variables=["iteration"],
        )
        with Task.Loop(10, name="Task2", loop_variable="iteration"):
            Task.HTTP.post(
                relative_url="/list",
                body=json.dumps({}),
                headers={"Content-Type": "application/json"},
                content_type="application/json",
                response_paths={"iteration": "$"},
                status_mapping={200: True},
                target=endpoints[0],
            )
