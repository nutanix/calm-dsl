"""
Calm DSL While Task Example

"""
import json

from calm.dsl.builtins import runbook
from calm.dsl.builtins import CalmTask, Auth
from calm.dsl.builtins import CalmEndpoint, ref
from calm.dsl.builtins import read_local_file, basic_cred

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

linux_endpoint = CalmEndpoint.Linux.ip([linux_ip], cred=LinuxCred)
windows_endpoint = CalmEndpoint.Windows.ip([windows_ip], cred=WindowsCred)
http_endpoint = CalmEndpoint.HTTP(URL, verify=False, auth=Auth.Basic(AUTH_USERNAME, AUTH_PASSWORD))


@runbook
def WhileTask(endpoints=[linux_endpoint, windows_endpoint, http_endpoint]):
    "Runbook Service example"
    while(10):
        with CalmTask.Decision.ssh(name="Task1", script="exit 0", target=ref(linux_endpoint)):
            def success():  # noqa
                CalmTask.Exec.ssh(name="SUCCESS1",
                                  script="echo 'SUCCESS'",
                                  target=ref(linux_endpoint))

            def failure():  # noqa
                CalmTask.Exec.ssh(name="FAILURE1",
                                  script="echo 'FAILURE'",
                                  target=ref(linux_endpoint))

        with CalmTask.Decision.ssh(name="Task2", script="exit 1", target=ref(linux_endpoint)):
            def success():  # noqa
                CalmTask.Exec.ssh(name="SUCCESS2",
                                  script="echo 'SUCCESS'",
                                  target=ref(linux_endpoint))

            def failure():  # noqa
                CalmTask.Exec.ssh(name="FAILURE2",
                                  script="echo 'FAILURE'",
                                  target=ref(linux_endpoint))

        CalmTask.Delay(15, name="Task3")
        CalmTask.Delay(15, name="Task4")
        CalmTask.HTTP.endpoint(
            "POST",
            name="Task5",
            relative_url="/list",
            body=json.dumps({}),
            headers={"Content-Type": "application/json"},
            content_type="application/json",
            status_mapping={200: True},
            target=ref(http_endpoint),
        )
        CalmTask.HTTP.endpoint(
            "POST",
            name="Task6",
            relative_url="/list",
            body=json.dumps({}),
            headers={"Content-Type": "application/json"},
            content_type="application/json",
            status_mapping={200: True},
            target=ref(http_endpoint),
        )
        while(CalmTask.While(10, name="Task7")):
            CalmTask.Exec.escript(script="print 'test'")
        while(CalmTask.While(10, name="Task8")):
            CalmTask.Exec.escript(script="print 'test'")
        CalmTask.Exec.escript(script="print 'test'", name="Task9")
        CalmTask.Exec.escript(script="print 'test'", name="Task10")
        CalmTask.Exec.ssh(script="echo 'test'", name="Task11", target=ref(linux_endpoint))
        CalmTask.Exec.ssh(script="echo 'test'", name="Task12", target=ref(linux_endpoint))
        CalmTask.Exec.powershell(script="echo 'test'", name="Task13", target=ref(windows_endpoint))
        CalmTask.Exec.powershell(script="echo 'test'", name="Task14", target=ref(windows_endpoint))
