"""
Generated provider DSL (.py)
"""

import json  # no_qa
import os  # no_qa

from calm.dsl.builtins import *  # no_qa
from calm.dsl.builtins import CalmTask as CalmVarTask
from calm.dsl.builtins.models.task import Status, ProviderTask as CalmTask
from calm.dsl.constants import CLOUD_PROVIDER as PROVIDER, RESOURCE_TYPE
from calm.dsl.runbooks import parallel, branch
from calm.dsl.runbooks import read_local_file


# Credentials
PROVIDER_CRED_cred_PASSWORD = "dummy_password"

PROVIDER_CRED_cred = basic_cred(
    username="dummy_username",
    password=PROVIDER_CRED_cred_PASSWORD,
    name="cred",
    type="PASSWORD",
)

DSL_CONFIG = json.loads(read_local_file(".tests/config.json"))
TUNNEL_1 = DSL_CONFIG["TUNNELS"]["TUNNEL_1"]["NAME"]
TUNNEL_2 = DSL_CONFIG["TUNNELS"]["TUNNEL_2"]["NAME"]

# ResourceTypes
class TestResourceType(ResourceType):

    resource_kind = "Compute"

    schemas = []

    variables = []

    @action
    def TestExecTask(type="resource_type_create"):

        PowershellVariable = CalmVariable.WithOptions.FromTask(
            CalmTask.Exec.powershell(
                name="",
                script="Write-Host 'Hello World'",
                ip="10.101.120.89",
                port=5985,
                connection_protocol="http",
                tunnel=Ref.Tunnel.Account(name=TUNNEL_2),
                cred=ref(PROVIDER_CRED_cred),
            ),
            label="",
            is_mandatory=False,
            is_hidden=False,
            description="",
        )
        ShellVariable = CalmVariable.WithOptions.FromTask(
            CalmTask.Exec.ssh(
                name="",
                script="echo 'Hello World'",
                ip="10.101.120.89",
                port=22,
                tunnel=Ref.Tunnel.Account(name=TUNNEL_2),
                cred=ref(PROVIDER_CRED_cred),
            ),
            label="",
            is_mandatory=False,
            is_hidden=False,
            description="",
        )
        EscriptVariable = CalmVariable.WithOptions.FromTask(
            CalmVarTask.Exec.escript.py3(
                name="",
                script="print('Hello World')",
                tunnel=Ref.Tunnel.Account(name=TUNNEL_2),
            ),
            label="",
            is_mandatory=False,
            is_hidden=False,
            description="",
        )

        CalmTask.Exec.escript.py3(
            name="Escript task",
            script="print('Hello World')",
            tunnel=Ref.Tunnel.Account(name=TUNNEL_2),
        )

        CalmTask.Exec.ssh(
            name="Shell Task",
            script="echo 'Hello World'",
            ip="10.101.120.89",
            port=22,
            tunnel=Ref.Tunnel.Account(name=TUNNEL_2),
            cred=ref(PROVIDER_CRED_cred),
        )

        CalmTask.Exec.powershell(
            name="Powershell task",
            script="Write-Host 'Hello World'",
            ip="10.101.120.89",
            port=5985,
            connection_protocol="http",
            tunnel=Ref.Tunnel.Account(name=TUNNEL_2),
            cred=ref(PROVIDER_CRED_cred),
        )

        CalmTask.Exec.python(
            name="Python task",
            script="print('Hello World')",
            ip="10.101.120.89",
            port=22,
            tunnel=Ref.Tunnel.Account(name=TUNNEL_2),
            cred=ref(PROVIDER_CRED_cred),
        )

    @action
    def TestSetVariableTask(type="resource_type_generic"):

        CalmTask.SetVariable.escript.py3(
            name="Escript task",
            script="print('Hello World')",
            tunnel=Ref.Tunnel.Account(name=TUNNEL_2),
            variables=["var`1", "var2"],
        )

        CalmTask.SetVariable.ssh(
            name="Shell task",
            script="echo 'Hello World'",
            ip="10.101.120.89",
            port=22,
            tunnel=Ref.Tunnel.Account(name=TUNNEL_2),
            cred=ref(PROVIDER_CRED_cred),
            variables=["var3", "var4"],
        )

        CalmTask.SetVariable.powershell(
            name="Powershell task",
            script="Write-Host 'Hello World'",
            ip="10.101.120.89",
            port=5985,
            connection_protocol="http",
            tunnel=Ref.Tunnel.Account(name=TUNNEL_2),
            cred=ref(PROVIDER_CRED_cred),
            variables=["var5", "var6"],
        )

        CalmTask.SetVariable.python(
            name="Python task",
            script="print('Hello World')",
            ip="10.101.120.89",
            port=22,
            tunnel=Ref.Tunnel.Account(name=TUNNEL_2),
            cred=ref(PROVIDER_CRED_cred),
            variables=["var7", "var8"],
        )

    @action
    def TestDecisionTask(type="resource_type_generic"):

        with CalmTask.Decision.escript.py3(
            name="Escript task",
            script="print('Hello World')",
            tunnel=Ref.Tunnel.Account(name=TUNNEL_2),
        ) as d0:

            if d0.ok:
                CalmTask.Exec.escript.py3(
                    name="Escript task 2",
                    script="print('Hello World')",
                )

            else:
                CalmTask.Exec.escript.py3(
                    name="Escript task 3",
                    script="print('Hello World')",
                )

        with CalmTask.Decision.ssh(
            name="Shell task",
            script="echo 'Hello World'",
            ip="10.101.120.89",
            port=22,
            tunnel=Ref.Tunnel.Account(name=TUNNEL_2),
            cred=ref(PROVIDER_CRED_cred),
        ) as d0:

            if d0.ok:
                CalmTask.Exec.escript.py3(
                    name="Escript task 4",
                    script="print('Hello World')",
                )

            else:
                CalmTask.Exec.escript.py3(
                    name="Escript task 5",
                    script="print('Hello World')",
                )

        with CalmTask.Decision.powershell(
            name="Powershell task",
            script="Write-Host 'Hello World'",
            ip="10.101.120.89",
            port=5985,
            connection_protocol="http",
            tunnel=Ref.Tunnel.Account(name=TUNNEL_2),
            cred=ref(PROVIDER_CRED_cred),
        ) as d0:

            if d0.ok:
                CalmTask.Exec.escript.py3(
                    name="Escript task 6",
                    script="print('Hello World')",
                )

            else:
                CalmTask.Exec.escript.py3(
                    name="Escript task 7",
                    script="print('Hello World')",
                )

        with CalmTask.Decision.python(
            name="Python task",
            script="print('Hello World')",
            ip="10.101.120.89",
            port=22,
            tunnel=Ref.Tunnel.Account(name=TUNNEL_2),
            cred=ref(PROVIDER_CRED_cred),
        ) as d0:

            if d0.ok:
                CalmTask.Exec.escript.py3(
                    name="Escript task 8",
                    script="print('Hello World')",
                )

            else:
                CalmTask.Exec.escript.py3(
                    name="Escript task 9",
                    script="print('Hello World')",
                ),

    @action
    def TestHTTPTask(type="resource_type_generic"):

        HttpDeleteVariable = CalmVariable.WithOptions.FromTask(
            CalmVarTask.HTTP.delete(
                "https://10.44.76.72:9440/api/nutanix/v3/clusters/list",
                headers={},
                secret_headers={},
                content_type="application/json",
                verify=False,
                response_code_status_map=[
                    HTTPResponseHandle.ResponseCode(
                        status=HTTPResponseHandle.TASK_STATUS.Success,
                        code_ranges=[{"start_code": 200, "end_code": 200}],
                    ),
                ],
                response_paths={"http_delete": "$.api_version"},
                name="",
                tunnel=Ref.Tunnel.Account(name=TUNNEL_2),
                body="{}",
            ),
            label="",
            is_mandatory=False,
            is_hidden=False,
            description="",
        )
        HttpPutVariable = CalmVariable.WithOptions.FromTask(
            CalmVarTask.HTTP.put(
                "https://10.44.76.72:9440/api/nutanix/v3/clusters/list",
                headers={},
                secret_headers={},
                content_type="application/json",
                verify=False,
                response_code_status_map=[
                    HTTPResponseHandle.ResponseCode(
                        status=HTTPResponseHandle.TASK_STATUS.Success,
                        code_ranges=[{"start_code": 200, "end_code": 200}],
                    ),
                ],
                response_paths={"http_put": "$.api_version"},
                name="",
                tunnel=Ref.Tunnel.Account(name=TUNNEL_2),
                body="{}",
            ),
            label="",
            is_mandatory=False,
            is_hidden=False,
            description="",
        )
        HttpPostVariable = CalmVariable.WithOptions.FromTask(
            CalmVarTask.HTTP.post(
                "https://10.44.76.72:9440/api/nutanix/v3/clusters/list",
                headers={},
                secret_headers={},
                content_type="application/json",
                verify=False,
                response_code_status_map=[
                    HTTPResponseHandle.ResponseCode(
                        status=HTTPResponseHandle.TASK_STATUS.Success,
                        code_ranges=[{"start_code": 200, "end_code": 200}],
                    ),
                ],
                response_paths={"http_post": "$.api_version"},
                name="",
                tunnel=Ref.Tunnel.Account(name=TUNNEL_2),
                body="{}",
            ),
            label="",
            is_mandatory=False,
            is_hidden=False,
            description="",
        )
        HttpGetVariable = CalmVariable.WithOptions.FromTask(
            CalmVarTask.HTTP.get(
                "https://10.44.76.72:9440/api/nutanix/v3/clusters/list",
                headers={},
                secret_headers={},
                content_type="application/json",
                verify=False,
                response_code_status_map=[
                    HTTPResponseHandle.ResponseCode(
                        status=HTTPResponseHandle.TASK_STATUS.Success,
                        code_ranges=[{"start_code": 200, "end_code": 200}],
                    ),
                ],
                response_paths={"http_get": "$.api_version"},
                name="",
                tunnel=Ref.Tunnel.Account(name=TUNNEL_2),
            ),
            label="",
            is_mandatory=False,
            is_hidden=False,
            description="",
        )

        CalmTask.HTTP.get(
            "https://10.44.76.72:9440/api/nutanix/v3/clusters/list",
            headers={},
            secret_headers={},
            content_type="application/json",
            verify=False,
            response_code_status_map=[
                HTTPResponseHandle.ResponseCode(
                    status=HTTPResponseHandle.TASK_STATUS.Success,
                    code_ranges=[{"start_code": 200, "end_code": 200}],
                ),
            ],
            response_paths={"X-Vault-Token": "ahv_linux"},
            name="HTTP Get Task",
            tunnel=Ref.Tunnel.Account(name=TUNNEL_2),
        )

        CalmTask.HTTP.post(
            "https://10.44.76.72:9440/api/nutanix/v3/clusters/list",
            headers={},
            secret_headers={},
            content_type="application/json",
            verify=False,
            response_code_status_map=[
                HTTPResponseHandle.ResponseCode(
                    status=HTTPResponseHandle.TASK_STATUS.Success,
                    code_ranges=[{"start_code": 200, "end_code": 200}],
                ),
            ],
            response_paths={"X-Vault-Token": "ahv_linux"},
            name="HTTP Post Task",
            tunnel=Ref.Tunnel.Account(name=TUNNEL_2),
            body="{}",
        )

        CalmTask.HTTP.put(
            "https://10.44.76.72:9440/api/nutanix/v3/clusters/list",
            headers={},
            secret_headers={},
            content_type="application/json",
            verify=False,
            response_code_status_map=[
                HTTPResponseHandle.ResponseCode(
                    status=HTTPResponseHandle.TASK_STATUS.Success,
                    code_ranges=[{"start_code": 200, "end_code": 200}],
                ),
            ],
            response_paths={"X-Vault-Token": "ahv_linux"},
            name="HTTP Put Task",
            tunnel=Ref.Tunnel.Account(name=TUNNEL_2),
            body="{}",
        )

        CalmTask.HTTP.delete(
            "https://10.44.76.72:9440/api/nutanix/v3/clusters/list",
            headers={},
            secret_headers={},
            content_type="application/json",
            verify=False,
            response_code_status_map=[
                HTTPResponseHandle.ResponseCode(
                    status=HTTPResponseHandle.TASK_STATUS.Success,
                    code_ranges=[{"start_code": 200, "end_code": 200}],
                ),
            ],
            response_paths={"X-Vault-Token": "ahv_linux"},
            name="HTTP Delete Task",
            tunnel=Ref.Tunnel.Account(name=TUNNEL_2),
            body="{}",
        )


class TestCustomProvider(CloudProvider):

    infra_type = "cloud"

    auth_schema_variables = [
        CalmVariable.Simple(
            "",
            label="Username",
            is_mandatory=True,
            is_hidden=False,
            runtime=True,
            description="",
            name="username",
        ),
        CalmVariable.Simple.Secret(
            PROVIDER_CRED_cred_PASSWORD,
            label="Password",
            is_mandatory=True,
            is_hidden=False,
            runtime=True,
            description="",
            name="password",
        ),
    ]

    variables = []

    endpoint_schema = ProviderEndpointSchema(type="NUTANIX_PC", variables=[])

    test_account = ProviderTestAccount(
        name="dsl_sample_test_account",
        variables=[
            CalmVariable.Simple(
                "10.44.76.72",
                label="Server",
                is_mandatory=True,
                is_hidden=False,
                runtime=True,
                description="",
                name="pc_server",
            ),
            CalmVariable.Simple.int(
                "9440",
                label="Port",
                regex="^[\\d]*$",
                validate_regex=True,
                is_mandatory=True,
                is_hidden=False,
                runtime=True,
                description="",
                name="pc_port",
            ),
            CalmVariable.Simple(
                "admin",
                label="Username",
                is_mandatory=True,
                is_hidden=False,
                runtime=True,
                description="",
                name="username",
            ),
            CalmVariable.Simple.Secret(
                PROVIDER_CRED_cred_PASSWORD,
                label="Password",
                is_mandatory=True,
                is_hidden=False,
                runtime=True,
                description="",
                name="password",
            ),
        ],
        tunnel=Ref.Tunnel.Account(name=TUNNEL_1),
    )

    credentials = [PROVIDER_CRED_cred]

    resource_types = [TestResourceType]

    @action
    def Verify(type="provider"):

        CalmTask.Exec.escript.py3(
            name="VerifyCredentials",
            script="print('Hello World')",
        )
