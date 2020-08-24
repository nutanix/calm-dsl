"""
Calm DSL Sample Runbook with runbook variable usecase

"""

from calm.dsl.runbooks import read_local_file
from calm.dsl.runbooks import runbook
from calm.dsl.runbooks import RunbookTask as Task, RunbookVariable as Variable, basic_cred
from calm.dsl.runbooks import CalmEndpoint as Endpoint


linux_ip = read_local_file(".tests/runbook_tests/vm_ip")
windows_ip = read_local_file(".tests/runbook_tests/windows_vm_ip")
CRED_USERNAME = read_local_file(".tests/runbook_tests/username")
CRED_WINDOWS_USERNAME = read_local_file(".tests/runbook_tests/windows_username")
CRED_PASSWORD = read_local_file(".tests/runbook_tests/password")

HTTP_AUTH_USERNAME = read_local_file(".tests/runbook_tests/auth_username")
HTTP_AUTH_PASSWORD = read_local_file(".tests/runbook_tests/auth_password")
HTTP_URL = read_local_file(".tests/runbook_tests/url")

http_endpoint = Endpoint.HTTP(
    HTTP_URL, verify=False, auth=Endpoint.Auth(HTTP_AUTH_USERNAME, HTTP_AUTH_PASSWORD),
)

LinuxCred = basic_cred(CRED_USERNAME, CRED_PASSWORD, name="endpoint_cred")
WindowsCred = basic_cred(CRED_WINDOWS_USERNAME, CRED_PASSWORD, name="endpoint_cred")

linux_endpoint = Endpoint.Linux.ip([linux_ip], cred=LinuxCred)
windows_endpoint = Endpoint.Windows.ip([windows_ip], cred=WindowsCred)


escript_code = """
print "@@{var1}@@"
if "@@{var1}@@" == "test":
    print "yes"
else:
    print "no"
print "@@{var2}@@"
if "@@{var2}@@" == "test":
    print "yes"
else:
    print "no"
print "Hello @@{firstname}@@ @@{lastname}@@"
"""

ssh_code = """
echo "hello there"
echo "@@{endpoint.name}@@"
"""


@runbook
def DslRunbookForMPI(endpoints=[windows_endpoint, linux_endpoint, http_endpoint]):
    "Runbook example with variables"

    var1 = Variable.Simple.Secret("test")  # noqa
    var2 = Variable.Simple.Secret("test", runtime=True)  # noqa
    firstname = Variable.Simple("FIRSTNAME", runtime=True)  # noqa
    lastname = Variable.Simple("LASTNAME")  # noqa

    Task.HTTP.get(
        name="HTTP_Task",
        headers={"Content-Type": "application/json"},
        content_type="application/json",
        status_mapping={200: True},
        target=endpoints[2],
    )

    Task.Exec.escript(name="ES_Task", script=escript_code)

    Task.Exec.ssh(name="SSH_Task",
                  script=ssh_code,
                  target=endpoints[1])

    Task.Exec.powershell(name="PowerShell_Task",
                         script=ssh_code)
