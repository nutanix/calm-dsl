"""
Calm DSL Decision Task with multiple target Example

"""
import json

from calm.dsl.runbooks import runbook
from calm.dsl.runbooks import RunbookTask as Task, RunbookVariable as Variable
from calm.dsl.runbooks import CalmEndpoint as Endpoint
from calm.dsl.runbooks import read_local_file, basic_cred
from calm.dsl.config import get_context

ContextObj = get_context()
server_config = ContextObj.get_server_config()
DSL_CONFIG = json.loads(read_local_file(".tests/config.json"))
linux_ip = read_local_file(".tests/runbook_tests/vm_ip")
linux_ip2 = DSL_CONFIG["EXISTING_MACHINE"]["IP_2"]
windows_ip = read_local_file(".tests/runbook_tests/windows_vm_ip")
CRED_USERNAME = read_local_file(".tests/runbook_tests/username")
CRED_WINDOWS_USERNAME = read_local_file(".tests/runbook_tests/windows_username")
CRED_PASSWORD = read_local_file(".tests/runbook_tests/password")
AUTH_USERNAME = read_local_file(".tests/runbook_tests/auth_username")
AUTH_PASSWORD = read_local_file(".tests/runbook_tests/auth_password")

LinuxCred = basic_cred(CRED_USERNAME, CRED_PASSWORD, name="linux_cred")
WindowsCred = basic_cred(CRED_WINDOWS_USERNAME, CRED_PASSWORD, name="windows_cred")

multi_target_linux_endpoint = Endpoint.Linux.ip([linux_ip, linux_ip2], cred=LinuxCred)
endpoint_with_multiple_urls = Endpoint.HTTP(
    ["@@{base}@@/endpoints", "@@{base}@@/blueprints", "@@{base}@@/runbooks"],
    auth=Endpoint.Auth(AUTH_USERNAME, AUTH_PASSWORD),
)

# script which prints all endpoint macros and passes for one ip and fails for rest
shell_script = """echo "@@{endpoint.name}@@, @@{endpoint.type}@@ , @@{endpoint.length}@@, @@{endpoint.index}@@, 
@@{endpoint.address}@@, @@{endpoint.port}@@, @@{endpoint.value_type}@@, @@{endpoint.addresses}@@, 
@@{endpoint.credential.username}@@"
echo "@@{endpoint.credential.secret}@@" 
string="@@{endpoint.address}@@"
if [[ $string == *"target_ip"* ]]; 
then
    echo "It's there!"  
    exit 0
fi
    exit 1"""

escript = """url = "@@{endpoint.base_url}@@"
if not "runbook" in url:
    print("Failing")
    exit(1)
print("Passing")
exit(0)"""

linux_ip_pass_script = shell_script.replace("target_ip", linux_ip)
linux_ip2_pass_script = shell_script.replace("target_ip", linux_ip2)


@runbook
def DecisionWithMultipleIpTarget(
    endpoints=[multi_target_linux_endpoint, endpoint_with_multiple_urls]
):

    base = Variable.Simple(  # noqa
        "https://{}:9440/api/nutanix/v3".format(server_config["pc_ip"])
    )

    with Task.Decision.ssh(script=linux_ip_pass_script, target=endpoints[0]) as d1:
        if d1.ok:
            Task.Exec.ssh(name="SUCCESS1_D1", script="date", inherit_target=True)

        else:
            Task.Exec.ssh(name="FAILURE1_D1", script="ls", inherit_target=True)

            with Task.Decision.ssh(
                script=linux_ip2_pass_script, inherit_target=True
            ) as d2:
                if d2.ok:
                    Task.Exec.ssh(
                        name="SUCCESS1_D2", script="date", inherit_target=True
                    )
                else:
                    Task.Exec.ssh(
                        name="FAILURE1_D2", script="date", inherit_target=True
                    )

    with Task.Decision.escript.py3(script=escript, target=endpoints[1]) as d3:
        if d3.ok:
            Task.HTTP.post(
                name="HTTPTask1",
                relative_url="/list",
                body=json.dumps({}),
                content_type="application/json",
                status_mapping={200: True},
                inherit_target=True,
            )

        else:
            Task.HTTP.post(
                name="HTTPTask2",
                relative_url="/list",
                body=json.dumps({}),
                content_type="application/json",
                status_mapping={200: True},
                inherit_target=True,
            )
