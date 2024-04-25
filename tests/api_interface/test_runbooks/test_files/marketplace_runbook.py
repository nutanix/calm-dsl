"""
Calm Runbook Definition for testing RUnbook Sharing

"""
import uuid
import pytest

from calm.dsl.runbooks import read_local_file
from calm.dsl.runbooks import runbook
from calm.dsl.runbooks import (
    RunbookTask as Task,
    RunbookVariable as Variable,
    basic_cred,
)
from calm.dsl.runbooks import CalmEndpoint as Endpoint
from utils import read_test_config, change_uuids, get_project_id_from_name


linux_ip = read_local_file(".tests/runbook_tests/vm_ip")
windows_ip = read_local_file(".tests/runbook_tests/windows_vm_ip")
CRED_USERNAME = read_local_file(".tests/runbook_tests/username")
CRED_WINDOWS_USERNAME = read_local_file(".tests/runbook_tests/windows_username")
CRED_PASSWORD = read_local_file(".tests/runbook_tests/password")

HTTP_AUTH_USERNAME = read_local_file(".tests/runbook_tests/auth_username")
HTTP_AUTH_PASSWORD = read_local_file(".tests/runbook_tests/auth_password")
HTTP_URL = read_local_file(".tests/runbook_tests/url1")

RBAC_PROJECT = read_local_file(".tests/runbook_tests/rbac_project")

http_endpoint = Endpoint.HTTP(HTTP_URL, verify=True)

LinuxCred = basic_cred(CRED_USERNAME, CRED_PASSWORD, name="endpoint_cred")
WindowsCred = basic_cred(CRED_WINDOWS_USERNAME, CRED_PASSWORD, name="endpoint_cred")

linux_endpoint = Endpoint.Linux.ip([linux_ip], cred=LinuxCred)
windows_endpoint = Endpoint.Windows.ip([windows_ip], cred=WindowsCred)


escript_code = """
print("@@{var1}@@")
if "@@{var1}@@" == "test":
    print("yes")
else:
    print("no")
print("@@{var2}@@")
if "@@{var2}@@" == "test":
    print("yes")
else:
    print("no")
print("Hello @@{firstname}@@ @@{lastname}@@")
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
        content_type="text/html",
        status_mapping={200: True},
        target=endpoints[2],
    )

    Task.Exec.escript.py3(name="ES_Task", script=escript_code)

    Task.Exec.ssh(name="SSH_Task", script=ssh_code, target=endpoints[1])

    Task.Exec.powershell(name="PowerShell_Task", script=ssh_code)


@runbook
def DslRunbookDynamicVariable():
    """Runbook example with dynamic variables"""

    escript_var = Variable.WithOptions.FromTask.int(  # NOQA
        Task.Exec.escript.py3(script="print('123')")
    )
    Task.Exec.escript.py3(name="ES_Task", script='print("Hello @@{escript_var}@@")')


@runbook
def DslWhileDecisionRunbookForMPI():
    "Runbook Service example"
    var = Variable.Simple("3")  # noqa
    with Task.Loop("@@{var}@@", name="WhileTask", loop_variable="iteration"):
        Task.Exec.escript.py3(name="Exec", script="""print("test")""")

    with Task.Decision.escript.py3(script="exit(0)") as d:

        if d.ok:
            Task.Exec.escript.py3(name="SUCCESS", script="print('SUCCESS')")

        else:
            Task.Exec.escript.py3(name="FAILURE", script="print('FAILURE')")


def create_project_endpoints(client, project_name=RBAC_PROJECT):
    linux_payload = read_test_config(file_name="linux_endpoint_payload.json")
    windows_payload = read_test_config(file_name="windows_endpoint_payload.json")
    http_payload = read_test_config(file_name="http_endpoint_payload.json")

    # Fix payload with correct data
    endpoint_resource = linux_payload["spec"]["resources"]
    endpoint_resource["attrs"]["values"] = [linux_ip]
    endpoint_resource["attrs"]["credential_definition_list"][0][
        "username"
    ] = CRED_USERNAME
    endpoint_resource["attrs"]["credential_definition_list"][0]["secret"][
        "value"
    ] = CRED_PASSWORD

    endpoint_resource = windows_payload["spec"]["resources"]
    endpoint_resource["attrs"]["values"] = [windows_ip]
    endpoint_resource["attrs"]["credential_definition_list"][0][
        "username"
    ] = CRED_WINDOWS_USERNAME
    endpoint_resource["attrs"]["credential_definition_list"][0]["secret"][
        "value"
    ] = CRED_PASSWORD

    project_uuid = get_project_id_from_name(client, project_name)
    project_endpoints = {}
    if project_uuid:
        for endpoint_payload in [linux_payload, windows_payload, http_payload]:
            endpoint = change_uuids(endpoint_payload, {})
            endpoint["metadata"]["project_reference"] = {
                "kind": "project",
                "uuid": project_uuid,
                "name": project_name,
            }
            endpoint["spec"]["name"] = "Endpoint_{}_{}".format(
                project_name, str(uuid.uuid4())[-10:]
            )
            # Endpoint Create
            res, err = client.endpoint.create(endpoint)
            if err:
                print(err)
                pytest.fail(err)
            ep = res.json()
            ep_state = ep["status"]["state"]
            ep_uuid = ep["metadata"]["uuid"]
            ep_name = ep["spec"]["name"]
            ep_type = ep["spec"]["resources"]["type"]
            print(
                ">> Endpoint created with name {} is in state: {}".format(
                    ep_name, ep_state
                )
            )
            project_endpoints[ep_type] = (ep_name, ep_uuid)

    return project_name, project_endpoints
